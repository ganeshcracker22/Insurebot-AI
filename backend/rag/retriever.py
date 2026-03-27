"""
RAG Retriever: fetches top-k relevant chunks from ChromaDB.
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


def retrieve(query: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Retrieve the top-k most relevant document chunks for a query.

    Args:
        query: The user's question.
        top_k: Number of results to return.

    Returns:
        List of dicts with 'text', 'source', 'page', 'company', 'distance'.
    """
    model = _get_model()
    collection = _get_collection()

    query_embedding = model.encode([query])[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, max(collection.count(), 1)),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
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
        }
    except Exception as exc:
        return {"error": str(exc)}
