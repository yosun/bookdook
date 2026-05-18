"""Typed configuration loader for BookDook.

Configuration is read from environment variables (with optional ``.env``
loading via ``python-dotenv``) and exposed as an immutable dataclass.

This module is the single source of truth for runtime configuration; no
other module should call ``os.getenv`` for app-level settings.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

from .errors import ConfigError

# Optional: load a local .env file if present. Never fail if dotenv is missing.
try:  # pragma: no cover - environment dependent
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


VALID_BACKENDS = {"ollama", "llamacpp", "llama", "llama.cpp", "dummy"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as e:
        raise ConfigError(f"Invalid integer for {name}={raw!r}") from e


def _env_str(name: str, default: str) -> str:
    val = os.getenv(name)
    return val if val not in (None, "") else default


@dataclass(frozen=True)
class OllamaConfig:
    model: str = "gemma2:2b"
    host: str = "127.0.0.1"
    port: int = 11434

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass(frozen=True)
class LlamaCppConfig:
    model_path: Optional[str] = None
    ctx_size: int = 2048
    n_threads: int = 4


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    max_request_bytes: int = 1 * 1024 * 1024  # 1 MiB cap on POST bodies


@dataclass(frozen=True)
class AppConfig:
    backend: str = "ollama"
    max_tokens: int = 512
    temperature: float = 0.2
    top_p: float = 0.9
    log_level: str = "INFO"
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    llamacpp: LlamaCppConfig = field(default_factory=LlamaCppConfig)
    server: ServerConfig = field(default_factory=ServerConfig)


def _load_temp(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as e:
        raise ConfigError(f"Invalid float for {name}={raw!r}") from e


def load_config() -> AppConfig:
    """Build an ``AppConfig`` from current environment variables."""
    backend = (_env_str("PLAIN_BACKEND", "ollama")).lower()
    if backend not in VALID_BACKENDS:
        raise ConfigError(
            f"PLAIN_BACKEND={backend!r} is not one of {sorted(VALID_BACKENDS)}"
        )

    max_tokens = _env_int("PLAIN_MAX_TOKENS", 512)
    if max_tokens <= 0:
        raise ConfigError("PLAIN_MAX_TOKENS must be > 0")

    ollama = OllamaConfig(
        model=_env_str("OLLAMA_MODEL", "gemma2:2b"),
        host=_env_str("OLLAMA_HOST", "127.0.0.1"),
        port=_env_int("OLLAMA_PORT", 11434),
    )

    llamacpp = LlamaCppConfig(
        model_path=os.getenv("LLAMACPP_MODEL_PATH") or None,
        ctx_size=_env_int("LLAMACPP_CTX_SIZE", 2048),
        n_threads=_env_int("LLAMACPP_N_THREADS", 4),
    )

    server = ServerConfig(
        host=_env_str("BOOKDOOK_HOST", "127.0.0.1"),
        port=_env_int("PORT", 8000),
        max_request_bytes=_env_int("BOOKDOOK_MAX_REQUEST_BYTES", 1 * 1024 * 1024),
    )

    return AppConfig(
        backend=backend,
        max_tokens=max_tokens,
        temperature=_load_temp("PLAIN_TEMPERATURE", 0.2),
        top_p=_load_temp("PLAIN_TOP_P", 0.9),
        log_level=_env_str("BOOKDOOK_LOG_LEVEL", "INFO"),
        ollama=ollama,
        llamacpp=llamacpp,
        server=server,
    )
