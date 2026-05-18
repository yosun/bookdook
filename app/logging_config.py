"""Centralized logging configuration for BookDook.

Use ``configure_logging()`` once at process startup (CLI / server / UI entrypoints)
to apply consistent, structured logs across the codebase.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Optional

_CONFIGURED = False


def configure_logging(level: Optional[str] = None) -> None:
    """Configure root logging once.

    Level resolution order:
    - explicit ``level`` argument
    - ``BOOKDOOK_LOG_LEVEL`` env var
    - ``INFO``
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved = (level or os.getenv("BOOKDOOK_LOG_LEVEL") or "INFO").upper()
    numeric = getattr(logging, resolved, logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    # Replace any pre-existing handlers to avoid duplicate logs in test runners.
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(handler)
    root.setLevel(numeric)

    # Quiet known-noisy libraries.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, configuring root on first use."""
    if not _CONFIGURED:
        configure_logging()
    return logging.getLogger(name)
