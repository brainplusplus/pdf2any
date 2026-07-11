"""List detection heuristics.

Detects bullet lists (•, -, *, ▪, ◦) and ordered lists (1., 2., a), b))
from text lines within a layout block.
"""

from __future__ import annotations

import re

from pdf2any.parser.layout_extractor import LayoutLine

# Patterns for list markers
_BULLET_PATTERN = re.compile(r"^\s*[•\-\*▪◦‣⁃]\s+(.+)")
_ORDERED_PATTERN = re.compile(r"^\s*(\d+)[.)]\s+(.+)")
_ALPHA_ORDERED_PATTERN = re.compile(r"^\s*([a-zA-Z])[.)]\s+(.+)")


def detect_list_type(lines: list[LayoutLine]) -> str | None:
    """Detect if a group of lines forms a list.

    Returns:
        "bullet" if all/most lines start with a bullet marker.
        "ordered" if all/most lines start with a number+period pattern.
        None if not a list.
    """
    if not lines:
        return None

    bullet_count = 0
    ordered_count = 0

    for line in lines:
        text = line.text.strip()
        if not text:
            continue
        if _BULLET_PATTERN.match(text):
            bullet_count += 1
        elif _ORDERED_PATTERN.match(text):
            ordered_count += 1

    total = len([ln for ln in lines if ln.text.strip()])
    if total == 0:
        return None

    if bullet_count / total >= 0.6:
        return "bullet"
    if ordered_count / total >= 0.6:
        return "ordered"

    return None


def extract_list_item_text(text: str) -> str:
    """Strip the list marker from a line of text."""
    text = text.strip()
    m = _BULLET_PATTERN.match(text)
    if m:
        return m.group(1)
    m = _ORDERED_PATTERN.match(text)
    if m:
        return m.group(2)
    m = _ALPHA_ORDERED_PATTERN.match(text)
    if m:
        return m.group(2)
    return text


def detect_list_start(lines: list[LayoutLine]) -> int:
    """Detect the starting number for an ordered list. Default 1."""
    for line in lines:
        m = _ORDERED_PATTERN.match(line.text.strip())
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                return 1
    return 1
