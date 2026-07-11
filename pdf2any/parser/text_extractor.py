"""Raw text extracted from a PDF page.

A ``RawTextSpan`` is a contiguous run of text with uniform font/style.
A ``RawPage`` holds all spans from a single page, plus page dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pdf2any.models.page import PageRef


@dataclass(slots=True)
class RawTextSpan:
    """A contiguous text run with uniform style on a page.

    Attributes:
        text: The actual text content.
        x0, y0, x1, y1: Bounding box in PDF user-space coordinates.
        font_size: Font size in points.
        font_name: Font name if available.
        bold: Whether the text is bold.
        italic: Whether the text is italic.
    """

    text: str
    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0
    font_size: float = 0.0
    font_name: str | None = None
    bold: bool = False
    italic: bool = False


@dataclass(slots=True)
class RawPage:
    """Raw extracted content from a single PDF page.

    Attributes:
        page_ref: Page reference (number, dimensions).
        spans: Text spans on this page, in reading order (top-to-bottom).
        raw_text: Full plain text of the page (concatenation of spans).
    """

    page_ref: PageRef
    spans: list[RawTextSpan] = field(default_factory=list)
    raw_text: str = ""
