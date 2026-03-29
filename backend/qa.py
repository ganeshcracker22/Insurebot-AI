"""
RAG QA: builds a prompt from retrieved context and queries Ollama.
"""

import logging
from typing import List, Dict, Any

from backend.rag.retriever import retrieve
from backend.lib.ollama import generate

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are InsureBot, a helpful and knowledgeable insurance assistant.
Answer the user's question based ONLY on the provided context from insurance policy documents.
If the context does not contain enough information, say so honestly.
Be concise, clear, and helpful. Do not make up policy details."""

NO_CONTEXT_RESPONSE = (
    "I don't have any insurance policy documents in my knowledge base yet. "
    "Please upload some policy PDFs using the **Upload PDFs** page, then ask your question again."
)


def build_prompt(question: str, context_chunks: List[Dict[str, Any]]) -> str:
    """Construct an RAG prompt with context + question."""
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        source_info = (
            f"[Source: {chunk['company']} – {chunk['source']}, page {chunk['page']}]"
        )
        context_parts.append(f"Context {i} {source_info}:\n{chunk['text']}")
    context_text = "\n\n".join(context_parts)

    return f"""{SYSTEM_PROMPT}

---
{context_text}
---

Question: {question}

Answer:"""


def answer(question: str, top_k: int = 3, model: str = "mistral") -> Dict[str, Any]:
    """
    Full RAG pipeline: retrieve context → build prompt → generate answer.

    Returns a dict with keys: answer, sources, question.
    """
    logger.info(f"RAG query: {question!r}")

    context_chunks = retrieve(question, top_k=top_k)

    # ── No documents in KB ────────────────────────────────────────────────────
    if not context_chunks:
        return {
            "question": question,
            "answer": NO_CONTEXT_RESPONSE,
            "sources": [],
        }

    prompt = build_prompt(question, context_chunks)

    try:
        response_text = generate(prompt, model=model)
    except RuntimeError as exc:
        logger.error(f"Ollama error: {exc}")
        response_text = (
            "I'm unable to answer right now because the AI service is unavailable. "
            "Please ensure Ollama is running (`ollama serve`) and try again."
        )

    sources = [
        {
            "company": c["company"],
            "source": c["source"],
            "page": c["page"],
        }
        for c in context_chunks
    ]

    return {
        "question": question,
        "answer": response_text,
        "sources": sources,
    }
