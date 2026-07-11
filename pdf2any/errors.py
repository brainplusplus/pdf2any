"""Typed exception hierarchy for pdf2any.

All errors carry a ``code`` (machine-readable string), a human ``message``,
and an ``exit_code`` that the CLI maps to process exit status.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ErrorInfo:
    """Structured error payload used in --json metadata output."""

    code: str
    message: str
    type: str


class PDF2AnyError(Exception):
    """Base error for all pdf2any failures.

    Attributes:
        code: Machine-readable error code (e.g. ``"PARSE_ERROR"``).
        exit_code: Process exit code the CLI should use.
    """

    code: str = "PDF2ANY_ERROR"
    exit_code: int = 1

    def __init__(self, message: str = "", *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code

    def to_info(self) -> ErrorInfo:
        """Return a serializable error info for --json output."""
        return ErrorInfo(
            code=self.code,
            message=self.message or self.__class__.__doc__ or self.code,
            type=self.__class__.__name__,
        )


class UsageError(PDF2AnyError):
    """Bad CLI arguments or flag combination."""

    code = "USAGE_ERROR"
    exit_code = 2


class PDFParseError(PDF2AnyError):
    """Failed to open or read the input PDF."""

    code = "PARSE_ERROR"
    exit_code = 1


class ExtractionError(PDF2AnyError):
    """Text or layout extraction from the PDF failed."""

    code = "EXTRACTION_ERROR"
    exit_code = 1


class NormalizationError(PDF2AnyError):
    """IR construction / semantic normalization failed."""

    code = "NORMALIZATION_ERROR"
    exit_code = 1


class RenderError(PDF2AnyError):
    """A renderer failed to produce output."""

    code = "RENDER_ERROR"
    exit_code = 1


class CapabilityError(PDF2AnyError):
    """A requested feature is not installed (e.g. OCR)."""

    code = "CAPABILITY_ERROR"
    exit_code = 3
