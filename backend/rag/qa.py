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


def build_prompt(question: str, context_chunks: List[Dict[str, Any]]) -> str:
    """Construct an RAG prompt with context + question."""
    if not context_chunks:
        context_text = "No relevant policy documents found."
    else:
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            source_info = f"[Source: {chunk['company']} – {chunk['source']}, page {chunk['page']}]"
            context_parts.append(f"Context {i} {source_info}:\n{chunk['text']}")
        context_text = "\n\n".join(context_parts)

    prompt = f"""{SYSTEM_PROMPT}

---
{context_text}
---

Question: {question}

Answer:"""
    return prompt


def answer(question: str, top_k: int = 3, model: str = "mistral") -> Dict[str, Any]:
    """
    Full RAG pipeline: retrieve context → build prompt → generate answer.

    Args:
        question: User's question.
        top_k: Number of context chunks to retrieve.
        model: Ollama model name.

    Returns:
        Dict with 'answer', 'sources', 'question'.
    """
    logger.info(f"RAG query: {question!r}")

    context_chunks = retrieve(question, top_k=top_k)
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
