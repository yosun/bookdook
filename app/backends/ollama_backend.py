import os
from typing import Optional, Dict, Any, List

from .base import LLMBackend


class OllamaBackend(LLMBackend):
    # Family prefix used for fallback resolution when the preferred model is
    # not installed locally. Any tag starting with this prefix (e.g.
    # "gemma4:e2b", "gemma4:9b-instruct") is considered a compatible
    # substitute.
    MODEL_FAMILY_PREFIX = "gemma4"

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
        preferred = os.getenv("OLLAMA_MODEL", "gemma4:e2b")
        self.model = self._resolve_model(preferred)

    # ------------------------------------------------------------------
    # Model resolution
    # ------------------------------------------------------------------
    def _list_local_models(self) -> List[str]:
        """Return the list of locally-installed Ollama model tags.

        Returns an empty list if the daemon is unreachable or the response
        shape is unexpected; callers should treat that as "unknown" and
        keep the preferred model name.
        """
        try:
            resp = self.client.list()
        except Exception:
            return []

        # The ollama python client has shifted shapes across versions:
        #   - dict: {"models": [{"name": "gemma4:e2b", ...}, ...]}
        #   - dict: {"models": [{"model": "gemma4:e2b", ...}, ...]}
        #   - object with .models attribute holding similar dicts/objects
        models_field = None
        if isinstance(resp, dict):
            models_field = resp.get("models")
        else:
            models_field = getattr(resp, "models", None)

        if not models_field:
            return []

        names: List[str] = []
        for m in models_field:
            name = None
            if isinstance(m, dict):
                name = m.get("name") or m.get("model")
            else:
                name = getattr(m, "name", None) or getattr(m, "model", None)
            if name:
                names.append(str(name))
        return names

    def _resolve_model(self, preferred: str) -> str:
        """Pick the preferred model if installed, else any compatible
        family member (gemma4:*). Falls back to the preferred name so the
        original error surfaces at generate() time if nothing matches.
        """
        installed = self._list_local_models()
        if not installed:
            # Daemon unreachable / unknown — keep preferred and let generate fail loudly.
            return preferred

        if preferred in installed:
            return preferred

        prefix = f"{self.MODEL_FAMILY_PREFIX}:"
        # Prefer exact family-prefix matches; fall back to the bare family
        # name as well (some installs tag models without an explicit size).
        candidates = [
            n for n in installed
            if n == self.MODEL_FAMILY_PREFIX or n.startswith(prefix)
        ]
        if candidates:
            # Deterministic choice: alphabetical order keeps behaviour stable
            # across runs without requiring a size-aware ranking.
            return sorted(candidates)[0]

        return preferred

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        # Use the simple generate endpoint for deterministic, offline generation.
        gen_kwargs = dict(
            model=self.model,
            prompt=prompt,
            options={
                "num_predict": max_tokens,
                "temperature": 0.2,
                "top_p": 0.9,
            },
        )
        try:
            try:
                # think=False disables reasoning-token consumption on models
                # like Gemma4 that would otherwise burn the entire token
                # budget on hidden chain-of-thought and return an empty
                # response. Older ollama clients reject the kwarg, so retry
                # without it.
                resp = self.client.generate(**gen_kwargs, think=False)
            except TypeError:
                resp = self.client.generate(**gen_kwargs)
            if isinstance(resp, dict):
                text = resp.get("response", "")
            else:
                text = getattr(resp, "response", "") or ""
            return (text or "").strip()
        except Exception as e:  # pragma: no cover - runtime dependent
            raise RuntimeError(f"Ollama generation failed for model '{self.model}': {e}")

