"""Structured logging configuration for pdf2any.

Configures the root ``pdf2any`` logger. ``--debug`` enables DEBUG level
with verbose stderr output; otherwise WARNING level is used.
"""

from __future__ import annotations

import logging
import sys

_LOGGER_NAME = "pdf2any"
_configured = False


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger under the pdf2any namespace."""
    if name:
        return logging.getLogger(f"{_LOGGER_NAME}.{name}")
    return logging.getLogger(_LOGGER_NAME)


def configure_logging(debug: bool = False) -> None:
    """Configure the pdf2any logger.

    Args:
        debug: If True, set DEBUG level with detailed format.
               If False, set WARNING level with minimal format.
    """
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)

    # Clear existing handlers to avoid duplicates on re-configure
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    if debug:
        logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        logger.setLevel(logging.WARNING)
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter("pdf2any: %(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    _configured = True
