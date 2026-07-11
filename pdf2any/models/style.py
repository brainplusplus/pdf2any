"""Style and font models used during extraction and heading detection."""

from __future__ import annotations

from dataclasses import dataclass, field

from pdf2any.ir import FontInfo

__all__ = ["FontInfo", "StyleHints"]


@dataclass(slots=True)
class StyleHints:
    """Aggregated style statistics for a page, used by heading detection.

    Attributes:
        median_font_size: The median font size across text spans.
        heading_threshold: Sizes at or above this are likely headings.
        dominant_font: The most common font name.
    """

    median_font_size: float = 0.0
    heading_threshold: float = 0.0
    dominant_font: str | None = None
    font_sizes: list[float] = field(default_factory=list)
