"""Optional table extraction using pdfplumber.

This module is only imported when the ``[tables]`` extra is installed.
It provides structured table extraction with cell bounding boxes,
which the normalizer converts to IR Table nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pdf2any.logging_config import get_logger

logger = get_logger("parser.tables")


@dataclass(slots=True)
class ExtractedTable:
    """A table extracted from a PDF page.

    Attributes:
        rows: List of rows, each a list of cell text strings.
        page: Page number (1-indexed).
        bbox: Bounding box of the table on the page (x0, y0, x1, y1).
    """

    rows: list[list[str]] = field(default_factory=list)
    page: int = 1
    bbox: tuple[float, float, float, float] | None = None


def extract_tables(
    pdf_source: str | bytes,
    page_numbers: list[int] | None = None,
) -> list[ExtractedTable]:
    """Extract tables from a PDF using pdfplumber.

    Args:
        pdf_source: Path to PDF or raw bytes.
        page_numbers: Specific pages to extract from (1-indexed). None = all.

    Returns:
        List of ExtractedTable objects.

    Raises:
        ImportError: If pdfplumber is not installed.
    """
    try:
        import pdfplumber  # type: ignore[import-untyped]
    except ImportError as e:
        raise ImportError(
            "Table extraction requires pdfplumber. "
            "Install with: pip install pdf2any[tables]"
        ) from e

    tables: list[ExtractedTable] = []

    if isinstance(pdf_source, bytes):
        import io

        source: Any = io.BytesIO(pdf_source)
    else:
        source = pdf_source

    with pdfplumber.open(source) as pdf:  # type: ignore[attr-defined]
        pages_to_process = pdf.pages
        if page_numbers:
            pages_to_process = [pdf.pages[p - 1] for p in page_numbers if 1 <= p <= len(pdf.pages)]

        for page in pages_to_process:
            page_tables = page.extract_tables()
            for tbl in page_tables:
                extracted = ExtractedTable(
                    rows=[[cell or "" for cell in row] for row in tbl],
                    page=page.page_number,
                )
                tables.append(extracted)

    logger.debug("Extracted %d tables from %d pages", len(tables), len(pages_to_process))
    return tables


def is_available() -> bool:
    """Check if pdfplumber is available."""
    try:
        import pdfplumber  # type: ignore[import-untyped]  # noqa: F401

        return True
    except ImportError:
        return False
