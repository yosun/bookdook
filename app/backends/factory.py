import os
from typing import Optional

from .base import LLMBackend, DummyBackend


def get_backend(preferred: Optional[str] = None) -> LLMBackend:
    """Return a local LLM backend according to env config.

    Order:
    - explicit preferred
    - env PLAIN_BACKEND
    - default 'ollama'
    Falls back to DummyBackend if imports/config fail.
    """
    choice = (preferred or os.getenv("PLAIN_BACKEND") or "ollama").lower()
    max_tokens = int(os.getenv("PLAIN_MAX_TOKENS", "512"))
    try:
        if choice == "ollama":
            from .ollama_backend import OllamaBackend

            return OllamaBackend(options={"max_tokens": max_tokens})
        elif choice in ("llamacpp", "llama", "llama.cpp"):
            from .llamacpp_backend import LlamaCppBackend

            return LlamaCppBackend(options={"max_tokens": max_tokens})
        elif choice == "dummy":
            return DummyBackend(options={"max_tokens": max_tokens})
    except Exception as e:  # pragma: no cover - environment dependent
        # Fallback to dummy with a note embedded in output
        return DummyBackend(options={"error": str(e), "max_tokens": max_tokens})

    # Unknown choice -> dummy
    return DummyBackend(options={"max_tokens": max_tokens})

