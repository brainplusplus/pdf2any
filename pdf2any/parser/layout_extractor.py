"""Layout extraction — converts raw text spans into layout-ordered blocks.

Uses vertical position (y0) to group spans into lines, then groups lines
into blocks separated by vertical gaps. This is the input to semantic
normalization.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pdf2any.parser.text_extractor import RawTextSpan


@dataclass(slots=True)
class LayoutLine:
    """A single line of text on a page, composed of one or more spans."""

    spans: list[RawTextSpan] = field(default_factory=list)
    y: float = 0.0  # Top Y coordinate (for ordering)
    text: str = ""

    def __post_init__(self) -> None:
        if self.spans and not self.text:
            self.text = "".join(s.text for s in self.spans)
            if self.spans:
                self.y = self.spans[0].y0


@dataclass(slots=True)
class LayoutBlock:
    """A group of adjacent lines, roughly corresponding to a paragraph."""

    lines: list[LayoutLine] = field(default_factory=list)
    y: float = 0.0
    font_size: float = 0.0  # Dominant font size of the block
    bold: bool = False
    italic: bool = False


def extract_layout(spans: list[RawTextSpan], page_height: float) -> list[LayoutLine]:
    """Group text spans into lines based on vertical proximity.

    Spans with similar y0 coordinates are grouped into a single line.
    Lines are returned in top-to-bottom reading order (highest y0 first
    in PDF coordinates, which is bottom-left origin, so we sort descending).

    Args:
        spans: Raw text spans from the page.
        page_height: Page height (for coordinate normalization if needed).

    Returns:
        List of LayoutLine in reading order (top to bottom).
    """
    if not spans:
        return []

    # Group spans by y proximity (within a threshold)
    y_threshold = 3.0  # points
    sorted_spans = sorted(spans, key=lambda s: -s.y0)  # top to bottom

    lines: list[LayoutLine] = []
    current_line_spans: list[RawTextSpan] = [sorted_spans[0]]
    current_y = sorted_spans[0].y0

    for span in sorted_spans[1:]:
        if abs(span.y0 - current_y) <= y_threshold:
            current_line_spans.append(span)
        else:
            # Finalize current line
            current_line_spans.sort(key=lambda s: s.x0)
            lines.append(LayoutLine(spans=current_line_spans))
            current_line_spans = [span]
            current_y = span.y0

    # Don't forget the last line
    current_line_spans.sort(key=lambda s: s.x0)
    lines.append(LayoutLine(spans=current_line_spans))

    return lines


def group_into_blocks(lines: list[LayoutLine]) -> list[LayoutBlock]:
    """Group lines into blocks separated by vertical gaps.

    A gap larger than 1.5x the typical line height starts a new block.
    """
    if not lines:
        return []

    blocks: list[LayoutBlock] = []
    current_lines: list[LayoutLine] = [lines[0]]

    for line in lines[1:]:
        gap = abs(current_lines[-1].y - line.y)
        line_height = _estimate_line_height(line)

        if gap > line_height * 1.5:
            # New block
            blocks.append(_make_block(current_lines))
            current_lines = [line]
        else:
            current_lines.append(line)

    # Final block
    blocks.append(_make_block(current_lines))

    return blocks


def _make_block(lines: list[LayoutLine]) -> LayoutBlock:
    """Create a LayoutBlock from a list of lines."""
    spans = [s for line in lines for s in line.spans]
    font_size = _median_font_size(spans) if spans else 0.0
    return LayoutBlock(
        lines=lines,
        y=lines[0].y if lines else 0.0,
        font_size=font_size,
        bold=any(s.bold for s in spans),
        italic=any(s.italic for s in spans),
    )


def _median_font_size(spans: list[RawTextSpan]) -> float:
    """Compute the median font size across spans."""
    if not spans:
        return 0.0
    sizes = sorted(s.font_size for s in spans)
    mid = len(sizes) // 2
    return sizes[mid]


def _estimate_line_height(line: LayoutLine) -> float:
    """Estimate the line height from span bounding boxes."""
    if not line.spans:
        return 12.0  # default
    heights = [abs(s.y1 - s.y0) for s in line.spans if s.y1 > s.y0]
    if not heights:
        return _median_font_size(line.spans) * 1.2
    return max(heights)
