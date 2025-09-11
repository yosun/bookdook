import os
from typing import Optional, Dict, Any

from .base import LLMBackend


class LlamaCppBackend(LLMBackend):
    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(options)
        try:
            from llama_cpp import Llama  # type: ignore
        except Exception as e:  # pragma: no cover - import error path
            raise RuntimeError(
                "llama-cpp-python not available. Install it to use llamacpp backend."
            ) from e
        model_path = os.getenv("LLAMACPP_MODEL_PATH")
        if not model_path or not os.path.exists(model_path):
            raise RuntimeError("LLAMACPP_MODEL_PATH is not set or file does not exist")
        ctx = int(os.getenv("LLAMACPP_CTX_SIZE", "2048"))
        n_threads = int(os.getenv("LLAMACPP_N_THREADS", "4"))
        # Lazy load: build the model instance
        self._llm = Llama(
            model_path=model_path,
            n_ctx=ctx,
            n_threads=n_threads,
            verbose=False,
        )

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        out = self._llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.2,
            top_p=0.9,
        )
        # llama-cpp returns a dict with 'choices'[0]['text'] when not using chat
        if isinstance(out, dict):
            try:
                return out["choices"][0]["text"].strip()
            except Exception:  # pragma: no cover - structure variations
                pass
        return str(out).strip()

