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
        self.client = ollama.Client(host=f"http://{host}:{port}")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        # Use the simple generate endpoint for deterministic, offline generation.
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

