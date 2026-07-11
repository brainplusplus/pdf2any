"""Semantic normalization — converts raw extracted pages into IR nodes.

This is where heuristic PDF-to-semantic conversion happens: heading
detection, list detection, table normalization, and paragraph grouping.
"""

from pdf2any.normalize.heading_detector import HeadingDetector
from pdf2any.normalize.normalizer import SemanticNormalizer

__all__ = ["HeadingDetector", "SemanticNormalizer"]
