from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMBackend(ABC):
    """Abstract interface for local LLM backends.

    Implementations must be fully offline and run locally.
    """

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        self.options = options or {}

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        raise NotImplementedError


class DummyBackend(LLMBackend):
    """Fallback offline backend producing templated outputs.

    Useful when real backends are unavailable.
    """

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        # A very small heuristic: return a generic, deterministic response
        # based on the start of the prompt to keep output useful in demos/tests.
        head = prompt.strip().splitlines()[0][:80]
        return (
            "[DUMMY RESPONSE]\n"
            f"Prompt: {head}\n\n"
            "Summary: This is a concise summary based on provided text.\n"
            "Checklist:\n- Identify key points\n- Verify facts\n- Follow next steps\n"
        )
