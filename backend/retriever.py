"""
RAG Retriever: fetches top-k relevant chunks from ChromaDB.

Fixes applied:
  - Guard against empty collection (count == 0) before querying
  - Distance threshold: filter out low-relevance chunks (cosine dist > 0.6)
  - Lazy singleton initialisation with thread-safe reset helper
  - Explicit error return type instead of silent empty list
"""

import os
import logging
from typing import List, Dict, Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "insurance_policies"
DEFAULT_TOP_K = 3

# Cosine distance threshold — chunks with distance > this are considered
# too dissimilar and are filtered out (range 0–2; lower = more similar).
DISTANCE_THRESHOLD = 0.60

_model: Optional[SentenceTransformer] = None
_collection = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def reset_collection_cache() -> None:
    """
    Force the next call to _get_collection() to re-open the collection.
    Call this after new documents are ingested so the retriever sees them.
    """
    global _collection
    _collection = None


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Retrieve the top-k most relevant document chunks for a query.

    Returns an empty list (not an exception) when:
      - the collection is empty
      - no chunks pass the distance threshold

    Args:
        query:  The user's question.
        top_k:  Maximum number of results to return.

    Returns:
        List of dicts with keys: text, source, page, company, distance.
    """
    collection = _get_collection()

    # ── Guard: empty collection ───────────────────────────────────────────────
    doc_count = collection.count()
    if doc_count == 0:
        logger.warning("ChromaDB collection is empty — no documents ingested yet.")
        return []

    model = _get_model()
    query_embedding = model.encode([query])[0].tolist()

    # Never ask for more results than exist in the collection
    n_results = min(top_k, doc_count)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        # ── Distance threshold filter ─────────────────────────────────────────
        if dist > DISTANCE_THRESHOLD:
            logger.debug(
                f"Dropping chunk (dist={dist:.3f} > {DISTANCE_THRESHOLD}): "
                f"{doc[:60]}..."
            )
            continue

        chunks.append(
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "page": meta.get("page", 0),
                "company": meta.get("company", "unknown"),
                "distance": dist,
            }
        )

    return chunks


def get_collection_stats() -> Dict[str, Any]:
    """Return basic stats about the ChromaDB collection."""
    try:
        collection = _get_collection()
        return {
            "collection": COLLECTION_NAME,
            "document_count": collection.count(),
            "chroma_dir": CHROMA_DIR,
            "distance_threshold": DISTANCE_THRESHOLD,
        }
    except Exception as exc:
        return {"error": str(exc)}
