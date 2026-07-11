"""SemanticNormalizer — converts raw extracted pages into an IRDocument.

This is the core heuristic stage: it takes RawPage objects from the parser,
runs layout extraction, heading/list/table detection, and builds a
structured IRDocument with proper block nodes.
"""

from __future__ import annotations

from typing import Any

from pdf2any.errors import NormalizationError
from pdf2any.ir import (
    Blockquote,
    BulletList,
    CodeBlock,
    Heading,
    IRDocument,
    ListItem,
    OrderedList,
    Page,
    PageBreak,
    Paragraph,
    PDFMetadata,
    Table,
    Text,
)
from pdf2any.logging_config import get_logger
from pdf2any.normalize.heading_detector import HeadingDetector
from pdf2any.normalize.list_detector import (
    detect_list_start,
    detect_list_type,
    extract_list_item_text,
)
from pdf2any.normalize.table_normalizer import normalize_table
from pdf2any.parser.layout_extractor import (
    LayoutBlock,
    extract_layout,
    group_into_blocks,
)
from pdf2any.parser.pdf_parser import PDFParser
from pdf2any.parser.table_extractor import ExtractedTable, extract_tables
from pdf2any.parser.text_extractor import RawPage

logger = get_logger("normalizer")


class SemanticNormalizer:
    """Converts raw PDF pages into a structured IRDocument.

    Args:
        heading_detector: Custom heading detector (uses default if None).
        enable_tables: If True, attempt table extraction.
    """

    def __init__(
        self,
        heading_detector: HeadingDetector | None = None,
        *,
        enable_tables: bool = True,
    ) -> None:
        self.heading_detector = heading_detector or HeadingDetector()
        self.enable_tables = enable_tables

    def normalize(
        self,
        raw_pages: list[RawPage],
        metadata: dict[str, Any],
        *,
        pdf_source: str | bytes | None = None,
        page_range: list[int] | None = None,
    ) -> IRDocument:
        """Build an IRDocument from raw extracted pages.

        Args:
            raw_pages: Raw pages from PDFParser.
            metadata: Metadata dict from PDFParser.
            pdf_source: Original PDF source (for table extraction if enabled).
            page_range: Page numbers for table extraction.

        Returns:
            A fully constructed IRDocument.

        Raises:
            NormalizationError: If normalization fails critically.
        """
        try:
            # Build IR metadata
            ir_meta = PDFMetadata(
                title=metadata.get("title"),
                author=metadata.get("author"),
                subject=metadata.get("subject"),
                creator=metadata.get("creator"),
                producer=metadata.get("producer"),
                creation_date=metadata.get("creation_date"),
                mod_date=metadata.get("mod_date"),
                page_count=metadata.get("page_count", len(raw_pages)),
                encrypted=metadata.get("encrypted", False),
            )

            # Extract tables if enabled and source available
            extracted_tables: list[ExtractedTable] = []
            if self.enable_tables and pdf_source is not None:
                try:
                    extracted_tables = extract_tables(pdf_source, page_range)
                    logger.debug("Extracted %d tables via pdfplumber", len(extracted_tables))
                except ImportError:
                    logger.debug("pdfplumber not available, skipping table extraction")
                except Exception as e:
                    logger.warning("Table extraction failed: %s", e)

            # Build IR pages
            ir_pages: list[Page] = []
            all_children: list[Paragraph | Heading | BulletList | OrderedList | Table | PageBreak] = []

            for raw_page in raw_pages:
                # Run layout extraction
                lines = extract_layout(raw_page.spans, raw_page.page_ref.height)
                blocks = group_into_blocks(lines)

                # Detect headings across all blocks
                heading_levels = self.heading_detector.detect_all(blocks)

                # Convert blocks to IR nodes
                page_children: list[Paragraph | Heading | BulletList | OrderedList | Table] = []
                for block, heading_level in zip(blocks, heading_levels, strict=False):
                    nodes = self._block_to_ir(block, heading_level)
                    page_children.extend(nodes)
                    all_children.extend(nodes)

                # Add page break between pages (except after the last)
                ir_pages.append(Page(page_number=raw_page.page_ref.number, children=page_children))

                if raw_page != raw_pages[-1]:
                    all_children.append(PageBreak())

            # Insert extracted tables — best effort: append at end of document
            # (A more sophisticated approach would place them by page/bbox)
            for ext_table in extracted_tables:
                ir_table = normalize_table(ext_table)
                # Fill in text content from extracted data
                _fill_table_text(ir_table, ext_table)
                all_children.append(ir_table)

            return IRDocument(metadata=ir_meta, pages=ir_pages, children=all_children)

        except NormalizationError:
            raise
        except Exception as e:
            raise NormalizationError(f"Semantic normalization failed: {e}") from e

    def _block_to_ir(
        self,
        block: LayoutBlock,
        heading_level: int | None,
    ) -> list[Paragraph | Heading | BulletList | OrderedList | Table]:
        """Convert a layout block to IR node(s)."""
        text = " ".join(line.text for line in block.lines).strip()

        if not text:
            return []

        # Heading
        if heading_level is not None:
            return [Heading(level=heading_level, content=[Text(text=text)])]

        # List detection
        list_type = detect_list_type(block.lines)
        if list_type == "bullet":
            items = []
            for line in block.lines:
                if line.text.strip():
                    item_text = extract_list_item_text(line.text)
                    items.append(ListItem(content=[Paragraph(content=[Text(text=item_text)])]))
            if items:
                return [BulletList(items=items)]

        if list_type == "ordered":
            items = []
            for line in block.lines:
                if line.text.strip():
                    item_text = extract_list_item_text(line.text)
                    items.append(ListItem(content=[Paragraph(content=[Text(text=item_text)])]))
            if items:
                start = detect_list_start(block.lines)
                return [OrderedList(items=items, start=start)]

        # Code block detection (monospace font + multiple lines)
        if _looks_like_code(block):
            code_text = "\n".join(line.text for line in block.lines)
            return [CodeBlock(content=code_text)]

        # Blockquote detection (lines starting with > or indented)
        if _looks_like_blockquote(block):
            quote_text = " ".join(
                line.text.lstrip("> ").strip() for line in block.lines
            )
            return [Blockquote(content=[Paragraph(content=[Text(text=quote_text)])])]

        # Default: paragraph
        return [Paragraph(content=[Text(text=text)])]


def _fill_table_text(ir_table: Table, ext_table: ExtractedTable) -> None:
    """Fill in text content for table cells from extracted data."""
    from pdf2any.ir import Text as IRText

    for ir_row, ext_row in zip(ir_table.rows, ext_table.rows, strict=False):
        for ir_cell, ext_cell in zip(ir_row.cells, ext_row, strict=False):
            if ext_cell and ext_cell.strip():
                ir_cell.content = [IRText(text=ext_cell.strip())]


def _looks_like_code(block: LayoutBlock) -> bool:
    """Heuristic: a block looks like code if it has monospace font indicators."""
    for line in block.lines:
        for span in line.spans:
            if span.font_name and any(
                name in span.font_name.lower()
                for name in ("mono", "courier", "consol", "code")
            ):
                return True
    return False


def _looks_like_blockquote(block: LayoutBlock) -> bool:
    """Heuristic: a block looks like a blockquote if lines start with > or are indented."""
    if not block.lines:
        return False
    quote_count = sum(1 for line in block.lines if line.text.strip().startswith(">"))
    return quote_count / len(block.lines) >= 0.5


# ---------------------------------------------------------------------------
# Convenience: full pipeline function
# ---------------------------------------------------------------------------


def parse_and_normalize(
    source: str | bytes,
    *,
    page_range: list[int] | None = None,
    enable_tables: bool = True,
) -> IRDocument:
    """Run the full pipeline: PDFParser → SemanticNormalizer → IRDocument.

    Args:
        source: Path to PDF or raw bytes.
        page_range: Optional page numbers to limit extraction.
        enable_tables: If True, attempt table extraction.

    Returns:
        A fully constructed IRDocument.
    """
    from pdf2any.utils.page_range import PageRange

    parser = PDFParser(enable_tables=enable_tables)
    rng = PageRange(pages=page_range or []) if page_range else None
    raw_pages, metadata = parser.parse(source, rng)

    normalizer = SemanticNormalizer(enable_tables=enable_tables)
    return normalizer.normalize(raw_pages, metadata, pdf_source=source, page_range=page_range)
