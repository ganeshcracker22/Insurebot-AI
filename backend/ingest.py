"""
Ingestion pipeline for insurance policy PDFs.

- Loads PDFs from /data/policies/  (batch mode)
- OR accepts a single in-memory bytes buffer  (upload mode)
- Extracts and cleans text
- Chunks text (500–800 tokens, 100 overlap)
- Generates embeddings with sentence-transformers (all-MiniLM-L6-v2)
- Stores in ChromaDB with metadata

Public API
----------
ingest(data_dir)          — batch-ingest all PDFs in a directory tree
ingest_file(pdf_bytes, filename, company)
                          — ingest a single PDF supplied as raw bytes
                            (used by the /upload endpoint)
"""

import io
import os
import re
import hashlib
import logging
from typing import List, Dict, Any, Optional

import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

# pypdf is used for in-memory loading (no temp file needed for small PDFs,
# but we write a temp file so PyPDFLoader can handle it uniformly)
import tempfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "policies")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
COLLECTION_NAME = "insurance_policies"

# Singleton embedding model — loaded once per process
_embed_model: Optional[SentenceTransformer] = None


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embed_model


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Remove excessive whitespace and common PDF artifacts."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


def _chunk_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split page-level text dicts into overlap chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: List[Dict[str, Any]] = []
    for doc in pages:
        parts = splitter.split_text(doc["text"])
        for i, part in enumerate(parts):
            if len(part.strip()) < 30:
                continue
            chunks.append(
                {
                    "text": part.strip(),
                    "source": doc["source"],
                    "page": doc["page"],
                    "company": doc["company"],
                    "chunk_index": i,
                }
            )
    return chunks


# ---------------------------------------------------------------------------
# ChromaDB helpers
# ---------------------------------------------------------------------------

def _get_collection():
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _upsert_chunks(chunks: List[Dict[str, Any]]) -> int:
    """Embed and upsert chunks into ChromaDB. Returns number stored."""
    if not chunks:
        return 0

    model = _get_embed_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)

    collection = _get_collection()
    batch_size = 100
    stored = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_emb = embeddings[i : i + batch_size].tolist()

        ids = [
            f"{c['company']}_{c['source']}_{c['page']}_{c['chunk_index']}"
            for c in batch
        ]
        metadatas = [
            {
                "source": c["source"],
                "page": c["page"],
                "company": c["company"],
                "chunk_index": c["chunk_index"],
            }
            for c in batch
        ]

        collection.upsert(
            ids=ids,
            embeddings=batch_emb,
            documents=[c["text"] for c in batch],
            metadatas=metadatas,
        )
        stored += len(batch)

    return stored


# ---------------------------------------------------------------------------
# Public API — single file
# ---------------------------------------------------------------------------

def ingest_file(
    pdf_bytes: bytes,
    filename: str,
    company: str = "uploaded",
) -> Dict[str, Any]:
    """
    Ingest a single PDF supplied as raw bytes.

    Used by the POST /upload FastAPI endpoint.

    Returns:
        {"pages": int, "chunks": int, "filename": str, "company": str}
    """
    # Write to a temp file so PyPDFLoader can work with it
    suffix = ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        raw_pages = loader.load()
    except Exception as exc:
        os.unlink(tmp_path)
        raise ValueError(f"Failed to parse PDF '{filename}': {exc}") from exc
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    pages: List[Dict[str, Any]] = []
    for page_doc in raw_pages:
        text = clean_text(page_doc.page_content)
        if len(text) < 50:
            continue
        pages.append(
            {
                "text": text,
                "source": filename,
                "page": page_doc.metadata.get("page", 0),
                "company": company,
            }
        )

    if not pages:
        raise ValueError(f"No readable text found in '{filename}'.")

    chunks = _chunk_pages(pages)
    stored = _upsert_chunks(chunks)

    logger.info(
        f"ingest_file: '{filename}' → {len(pages)} pages, {stored} chunks stored"
    )
    return {
        "filename": filename,
        "company": company,
        "pages": len(pages),
        "chunks": stored,
    }


# ---------------------------------------------------------------------------
# Public API — batch directory
# ---------------------------------------------------------------------------

def load_pdfs(data_dir: str) -> List[Dict[str, Any]]:
    """Recursively load all PDFs from data_dir."""
    documents: List[Dict[str, Any]] = []

    for company in os.listdir(data_dir):
        company_path = os.path.join(data_dir, company)
        if not os.path.isdir(company_path):
            continue

        for filename in os.listdir(company_path):
            if not filename.lower().endswith(".pdf"):
                continue

            filepath = os.path.join(company_path, filename)
            logger.info(f"Loading: {filepath}")

            try:
                loader = PyPDFLoader(filepath)
                raw_pages = loader.load()
                for page_doc in raw_pages:
                    text = clean_text(page_doc.page_content)
                    if len(text) < 50:
                        continue
                    documents.append(
                        {
                            "text": text,
                            "source": filename,
                            "page": page_doc.metadata.get("page", 0),
                            "company": company,
                            "filepath": filepath,
                        }
                    )
            except Exception as exc:
                logger.warning(f"Failed to load {filepath}: {exc}")

    logger.info(f"Loaded {len(documents)} pages from PDFs")
    return documents


def ingest(data_dir: str = DATA_DIR) -> None:
    """Full batch ingestion pipeline: load → chunk → embed → store."""
    os.makedirs(CHROMA_DIR, exist_ok=True)

    logger.info("Loading PDFs...")
    documents = load_pdfs(data_dir)

    if not documents:
        logger.warning(f"No PDFs found in {data_dir}. Add PDFs and re-run.")
        return

    logger.info("Chunking documents...")
    chunks = _chunk_pages(documents)

    if not chunks:
        logger.warning("No valid chunks produced.")
        return

    stored = _upsert_chunks(chunks)
    logger.info(
        f"Ingestion complete. {stored} chunks stored in ChromaDB at {CHROMA_DIR}"
    )


if __name__ == "__main__":
    ingest()
