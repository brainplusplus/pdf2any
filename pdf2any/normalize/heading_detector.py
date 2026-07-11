"""Heading detection heuristics.

Uses font size relative to the page median, bold weight, and short line
length to detect heading-like text blocks. Maps detected headings to
levels 1–6 based on font size ratios.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from pdf2any.models.style import StyleHints
from pdf2any.parser.layout_extractor import LayoutBlock


@dataclass(slots=True)
class HeadingDetector:
    """Detects headings from layout blocks using font-size heuristics.

    The detector computes the median font size across all blocks, then
    classifies blocks as headings if their font size exceeds a threshold
    or if they are bold and short.
    """

    # A block is a heading if its font_size >= median * this factor
    size_ratio_threshold: float = 1.3
    # A bold block shorter than this (in chars) is likely a heading
    short_bold_max_length: int = 80

    def compute_style_hints(self, blocks: list[LayoutBlock]) -> StyleHints:
        """Compute style statistics from layout blocks.

        Uses the **mode** (most common) font size as the body text baseline,
        not the median. This prevents headings from inflating the baseline
        when there are few blocks. If mode fails, falls back to median.
        """
        all_sizes: list[float] = []
        font_names: list[str] = []

        for block in blocks:
            for line in block.lines:
                for span in line.spans:
                    if span.font_size > 0:
                        all_sizes.append(span.font_size)
                    if span.font_name:
                        font_names.append(span.font_name)

        if not all_sizes:
            return StyleHints()

        # Use mode (most common size) as baseline — more robust than median
        # for documents with a few large headings among many body text blocks.
        # If there's only one unique size, fall back to 12pt (standard body text).
        unique_sizes = set(all_sizes)
        if len(unique_sizes) <= 1:
            # Single font size — can't determine relative scale.
            # Use 12pt as the assumed body text baseline.
            baseline = 12.0
        else:
            try:
                baseline = statistics.mode(all_sizes)
            except statistics.StatisticsError:
                baseline = statistics.median(all_sizes)

        threshold = baseline * self.size_ratio_threshold

        dominant_font = None
        if font_names:
            try:
                dominant_font = statistics.mode(font_names)
            except statistics.StatisticsError:
                dominant_font = font_names[0] if font_names else None

        return StyleHints(
            median_font_size=baseline,  # Actually the mode — used as baseline
            heading_threshold=threshold,
            dominant_font=dominant_font,
            font_sizes=all_sizes,
        )

    def detect_level(
        self,
        block: LayoutBlock,
        style: StyleHints,
    ) -> int | None:
        """Detect if a block is a heading and return its level (1–6).

        Returns None if the block is not a heading.

        Heuristic:
            1. If font_size >= heading_threshold → heading, level by size ratio.
            2. If bold and short → heading level 4 (conservative).
            3. Otherwise → not a heading.
        """
        text = " ".join(line.text for line in block.lines).strip()
        if not text:
            return None

        font_size = block.font_size or style.median_font_size
        baseline = style.median_font_size  # This is the mode (body text size)

        if baseline <= 0:
            return None

        ratio = font_size / baseline

        # Size-based heading detection
        if font_size >= style.heading_threshold:
            if ratio >= 2.0:
                return 1
            if ratio >= 1.6:
                return 2
            if ratio >= 1.4:
                return 3
            return 4

        # Bold + short → heading (conservative level)
        if (
            block.bold
            and len(text) <= self.short_bold_max_length
            and not text.endswith(".")
            and _looks_like_title(text)
        ):
            return 5

        return None

    def detect_all(self, blocks: list[LayoutBlock]) -> list[int | None]:
        """Detect heading levels for all blocks at once.

        Returns a list parallel to blocks, with int level or None.
        """
        style = self.compute_style_hints(blocks)
        return [self.detect_level(block, style) for block in blocks]


def _looks_like_title(text: str) -> bool:
    """Heuristic: text looks like a title/heading if most words are capitalized."""
    words = text.split()
    if len(words) > 15:
        return False  # Too long to be a heading
    if not words:
        return False
    capitalized = sum(1 for w in words if w and w[0].isupper())
    return capitalized / len(words) >= 0.6
