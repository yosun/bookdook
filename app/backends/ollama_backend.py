import os
from typing import Optional, Dict, Any

from .base import LLMBackend


class OllamaBackend(LLMBackend):
    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(options)
        try:
            import ollama  # type: ignore
        except Exception as e:  # pragma: no cover - import error path
            raise RuntimeError(
                "Ollama Python package not available. Install 'ollama'."
            ) from e
        self._ollama = ollama
        host = os.getenv("OLLAMA_HOST", "127.0.0.1")
        port = int(os.getenv("OLLAMA_PORT", "11434"))
        self.client = self._ollama.Client(host=f"http://{host}:{port}")
        # Default to a local Gemma4 model; can override via OLLAMA_MODEL
        self.model = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        # Use the simple generate endpoint for deterministic, offline generation.
        try:
            resp = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "num_predict": max_tokens,
                    "temperature": 0.2,
                    "top_p": 0.9,
                },
            )
            return resp.get("response", "").strip()
        except Exception as e:  # pragma: no cover - runtime dependent
            raise RuntimeError(f"Ollama generation failed for model '{self.model}': {e}")

