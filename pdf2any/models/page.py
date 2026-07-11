"""Page-level reference models.

``BoundingBox`` and ``SourceLocation`` are re-exported from the IR module
to avoid duplication. ``PageRef`` is a lightweight handle to a PDF page
used during extraction before the full IR Page is constructed.
"""

from __future__ import annotations

from dataclasses import dataclass

from pdf2any.ir import BoundingBox, SourceLocation

__all__ = ["BoundingBox", "PageRef", "SourceLocation"]


@dataclass(slots=True)
class PageRef:
    """A lightweight reference to a PDF page during extraction.

    Attributes:
        number: 1-indexed page number.
        width: Page width in PDF points.
        height: Page height in PDF points.
    """

    number: int
    width: float
    height: float
