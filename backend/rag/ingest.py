"""
Ingestion pipeline for insurance policy PDFs.

- Loads PDFs from /data/policies/
- Extracts and cleans text
- Chunks text (500–800 tokens, 100 overlap)
- Generates embeddings with sentence-transformers (all-MiniLM-L6-v2)
- Stores in ChromaDB with metadata
"""

import os
import re
import logging
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "policies")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
COLLECTION_NAME = "insurance_policies"


def clean_text(text: str) -> str:
    """Remove excessive whitespace and common PDF artifacts."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()
    return text


def load_pdfs(data_dir: str) -> List[Dict[str, Any]]:
    """
    Recursively load all PDFs from data_dir.
    Returns list of {text, source, page, company} dicts.
    """
    documents = []

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
                pages = loader.load()

                for page_doc in pages:
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
                continue

    logger.info(f"Loaded {len(documents)} pages from PDFs")
    return documents


def chunk_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split documents into chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in documents:
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

    logger.info(f"Created {len(chunks)} chunks from {len(documents)} pages")
    return chunks


def get_chroma_collection():
    """Get or create the ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return client, collection


def ingest(data_dir: str = DATA_DIR):
    """Full ingestion pipeline: load → chunk → embed → store."""
    os.makedirs(CHROMA_DIR, exist_ok=True)

    logger.info("Loading PDFs...")
    documents = load_pdfs(data_dir)

    if not documents:
        logger.warning(f"No PDFs found in {data_dir}. Add PDFs and re-run.")
        return

    logger.info("Chunking documents...")
    chunks = chunk_documents(documents)

    if not chunks:
        logger.warning("No valid chunks produced.")
        return

    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    logger.info("Generating embeddings...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)

    logger.info("Storing in ChromaDB...")
    client, collection = get_chroma_collection()

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_embeddings = embeddings[i : i + batch_size].tolist()

        ids = [
            f"{c['company']}_{c['source']}_{c['page']}_{c['chunk_index']}"
            for c in batch_chunks
        ]
        metadatas = [
            {
                "source": c["source"],
                "page": c["page"],
                "company": c["company"],
                "chunk_index": c["chunk_index"],
            }
            for c in batch_chunks
        ]

        collection.upsert(
            ids=ids,
            embeddings=batch_embeddings,
            documents=texts[i : i + batch_size],
            metadatas=metadatas,
        )

    logger.info(
        f"Ingestion complete. {len(chunks)} chunks stored in ChromaDB at {CHROMA_DIR}"
    )


if __name__ == "__main__":
    ingest()
