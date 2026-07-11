"""Shared domain models (non-IR) used by parser, normalizer, and backends."""

from pdf2any.models.metadata import PDFMetadata
from pdf2any.models.page import BoundingBox, PageRef, SourceLocation
from pdf2any.models.style import FontInfo, StyleHints

__all__ = [
    "BoundingBox",
    "FontInfo",
    "PageRef",
    "PDFMetadata",
    "SourceLocation",
    "StyleHints",
]
