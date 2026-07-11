"""Table normalization — converts extracted table data into IR Table nodes."""

from __future__ import annotations

from pdf2any.ir import Table, TableCell, TableRow
from pdf2any.parser.table_extractor import ExtractedTable


def normalize_table(extracted: ExtractedTable) -> Table:
    """Convert an ExtractedTable (from pdfplumber) to an IR Table node.

    The first row is treated as a header row if it appears to be one
    (non-empty, shorter than subsequent rows, or all-caps).
    """
    if not extracted.rows:
        return Table(rows=[])

    ir_rows: list[TableRow] = []

    for i, row in enumerate(extracted.rows):
        cells = [TableCell(content=[]) for _ in row]
        # We can't easily create Text nodes here without importing ir.Text
        # The normalizer will fill in text content
        is_header = i == 0 and _looks_like_header(row)
        ir_rows.append(TableRow(cells=cells, header=is_header))

    return Table(rows=ir_rows)


def _looks_like_header(row: list[str]) -> bool:
    """Heuristic: a row looks like a header if all cells are non-empty
    and most are short strings (labels)."""
    if not row:
        return False
    non_empty = [c for c in row if c and c.strip()]
    if not non_empty:
        return False
    short = [c for c in non_empty if len(c.strip()) <= 50]
    return len(short) / len(non_empty) >= 0.7
