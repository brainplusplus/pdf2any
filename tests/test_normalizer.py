"""Tests for the normalizer — heading/list/table detection heuristics."""

from __future__ import annotations

from pdf2any.ir import (
    BulletList,
    Heading,
    OrderedList,
    Paragraph,
    Text,
)
from pdf2any.normalize.heading_detector import HeadingDetector
from pdf2any.normalize.list_detector import detect_list_type, extract_list_item_text
from pdf2any.parser.layout_extractor import LayoutBlock, LayoutLine
from pdf2any.parser.text_extractor import RawTextSpan


def _make_span(text: str, font_size: float = 12.0, bold: bool = False) -> RawTextSpan:
    return RawTextSpan(text=text, font_size=font_size, bold=bold)


def _make_line(text: str, font_size: float = 12.0, bold: bool = False) -> LayoutLine:
    return LayoutLine(spans=[_make_span(text, font_size, bold)])


def _make_block(text: str, font_size: float = 12.0, bold: bool = False) -> LayoutBlock:
    return LayoutBlock(lines=[_make_line(text, font_size, bold)], font_size=font_size, bold=bold)


class TestHeadingDetector:
    """Tests for heading detection heuristics."""

    def test_large_font_detected_as_heading(self):
        detector = HeadingDetector()
        blocks = [
            _make_block("Normal text", font_size=12.0),
            _make_block("Big Title", font_size=24.0),
        ]
        levels = detector.detect_all(blocks)
        assert levels[1] is not None
        assert levels[1] <= 2  # Large font → level 1 or 2

    def test_normal_text_not_heading(self):
        detector = HeadingDetector()
        blocks = [_make_block("Normal paragraph text here.", font_size=12.0)]
        levels = detector.detect_all(blocks)
        assert levels[0] is None

    def test_bold_short_text_as_heading(self):
        detector = HeadingDetector()
        blocks = [
            _make_block("Normal text", font_size=12.0),
            _make_block("Section Title", font_size=12.0, bold=True),
        ]
        levels = detector.detect_all(blocks)
        # Bold + short + title case → heading level 5
        assert levels[1] is not None

    def test_heading_level_in_range(self):
        detector = HeadingDetector()
        blocks = [_make_block("T", font_size=36.0)]
        levels = detector.detect_all(blocks)
        assert levels[0] is not None
        assert 1 <= levels[0] <= 6

    def test_empty_blocks(self):
        detector = HeadingDetector()
        levels = detector.detect_all([])
        assert levels == []


class TestListDetector:
    """Tests for list detection."""

    def test_bullet_list_detection(self):
        lines = [
            _make_line("• First item"),
            _make_line("• Second item"),
            _make_line("• Third item"),
        ]
        assert detect_list_type(lines) == "bullet"

    def test_ordered_list_detection(self):
        lines = [
            _make_line("1. First"),
            _make_line("2. Second"),
            _make_line("3. Third"),
        ]
        assert detect_list_type(lines) == "ordered"

    def test_not_a_list(self):
        lines = [
            _make_line("Just a normal paragraph."),
            _make_line("With multiple lines of text."),
        ]
        assert detect_list_type(lines) is None

    def test_extract_bullet_text(self):
        assert extract_list_item_text("• Hello") == "Hello"

    def test_extract_ordered_text(self):
        assert extract_list_item_text("3. Third") == "Third"

    def test_extract_plain_text(self):
        assert extract_list_item_text("Plain text") == "Plain text"
