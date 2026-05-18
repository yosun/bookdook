"""Custom exception hierarchy for BookDook.

All exceptions raised by application code should inherit from
``BookDookError`` so callers can catch a single base type when needed.
"""
from __future__ import annotations


class BookDookError(Exception):
    """Base class for all BookDook errors."""


class BackendError(BookDookError):
    """Raised when an LLM backend fails to load or generate."""


class BackendUnavailableError(BackendError):
    """Raised when a backend cannot be initialized (missing deps, model, etc.)."""


class ConfigError(BookDookError):
    """Raised on invalid or missing configuration."""


class SchemaError(BookDookError):
    """Raised when a form schema is invalid."""


class ContentError(BookDookError):
    """Raised when input content (PDF, letter, etc.) cannot be processed."""
