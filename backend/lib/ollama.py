"""
Ollama client for local LLM inference.
Communicates with Ollama running at http://localhost:11434.
"""

import json
import logging
from typing import List
import requests

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "mistral"


def generate(prompt: str, model: str = DEFAULT_MODEL, stream: bool = False) -> str:
    """
    Send a prompt to Ollama and return the generated text.

    Args:
        prompt: The input prompt.
        model: Ollama model name (default: mistral).
        stream: Whether to use streaming (default: False).

    Returns:
        Generated text string.

    Raises:
        RuntimeError: If the Ollama request fails.
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": stream,
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        if stream:
            full_text = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    full_text += data.get("response", "")
                    if data.get("done"):
                        break
            return full_text.strip()
        else:
            data = response.json()
            return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is running: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama request timed out. The model may be loading.")
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc


def list_models() -> List[str]:
    """Return list of locally available Ollama models."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        response.raise_for_status()
        data = response.json()
        return [m["name"] for m in data.get("models", [])]
    except requests.exceptions.RequestException:
        return []


def is_available() -> bool:
    """Check if Ollama service is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False
