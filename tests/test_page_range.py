"""Tests for page range parsing."""

from __future__ import annotations

import pytest

from pdf2any.utils.page_range import PageRange, parse_page_range


class TestParsePageRange:
    """Tests for page range string parsing."""

    def test_single_page(self):
        pr = parse_page_range("5")
        assert pr.pages == [5]
        assert pr.explicit is True

    def test_range(self):
        pr = parse_page_range("1-5")
        assert pr.pages == [1, 2, 3, 4, 5]

    def test_comma_separated(self):
        pr = parse_page_range("1,3,5")
        assert pr.pages == [1, 3, 5]

    def test_mixed(self):
        pr = parse_page_range("1-3,7,9-11")
        assert pr.pages == [1, 2, 3, 7, 9, 10, 11]

    def test_reversed_range(self):
        pr = parse_page_range("5-1")
        assert pr.pages == [1, 2, 3, 4, 5]

    def test_deduplicates(self):
        pr = parse_page_range("1-3,2-4")
        assert pr.pages == [1, 2, 3, 4]

    def test_empty_string(self):
        pr = parse_page_range("")
        assert pr.pages == []
        assert pr.explicit is False

    def test_none(self):
        pr = parse_page_range(None)
        assert pr.pages == []
        assert pr.explicit is False

    def test_invalid_number(self):
        with pytest.raises(ValueError):
            parse_page_range("abc")

    def test_invalid_range(self):
        with pytest.raises(ValueError):
            parse_page_range("1-2-3")

    def test_start_end(self):
        pr = parse_page_range(None, start=3, end=5)
        assert pr.pages == [3, 4, 5]
        assert pr.explicit is True

    def test_start_only(self):
        pr = parse_page_range(None, start=3)
        assert pr.pages == list(range(3, 1000000))
        assert pr.explicit is True

    def test_start_end_intersects_with_pages(self):
        pr = parse_page_range("1-10", start=3, end=5)
        assert pr.pages == [3, 4, 5]


class TestPageRangeSelect:
    """Tests for PageRange.select()."""

    def test_select_all_when_empty(self):
        pr = PageRange()
        assert pr.select(5) == [1, 2, 3, 4, 5]

    def test_select_filters_out_of_range(self):
        pr = PageRange(pages=[1, 3, 5, 10])
        assert pr.select(5) == [1, 3, 5]

    def test_select_empty(self):
        pr = PageRange()
        assert pr.select(0) == []

    def test_is_empty(self):
        assert PageRange().is_empty() is True
        assert PageRange(pages=[1]).is_empty() is False
