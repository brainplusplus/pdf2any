"""PDFParser — the primary PDF reading and extraction orchestrator.

Uses:
    - pypdfium2 for page rendering and text extraction (BSD-3)
    - pypdf for metadata, encryption detection (BSD)
    - pdfplumber (optional) for table extraction (MIT)

The parser produces a list of RawPage objects, which the SemanticNormalizer
converts into an IRDocument.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pdf2any.errors import PDFParseError
from pdf2any.logging_config import get_logger
from pdf2any.models.page import PageRef
from pdf2any.parser.text_extractor import RawPage, RawTextSpan
from pdf2any.utils.page_range import PageRange

logger = get_logger("parser")


class PDFParser:
    """Orchestrates PDF reading, text extraction, and metadata collection.

    Args:
        enable_tables: If True, attempt table extraction with pdfplumber
                       (requires the ``[tables]`` extra to be installed).
    """

    def __init__(self, *, enable_tables: bool = True) -> None:
        self.enable_tables = enable_tables

    def parse(
        self,
        source: str | bytes,
        page_range: PageRange | None = None,
    ) -> tuple[list[RawPage], dict[str, Any]]:
        """Parse a PDF and extract raw text pages and metadata.

        Args:
            source: Path to PDF file or raw bytes.
            page_range: Optional page range to limit extraction.

        Returns:
            Tuple of (raw_pages, metadata_dict).

        Raises:
            PDFParseError: If the PDF cannot be opened or read.
        """
        try:
            import pypdfium2 as pdfium  # type: ignore[import-untyped]
        except ImportError as e:
            raise PDFParseError(
                "pypdfium2 is required. Install with: pip install pypdfium2"
            ) from e

        logger.debug("Opening PDF source: %s", _describe_source(source))

        try:
            if isinstance(source, bytes):
                pdf = pdfium.PdfDocument(source)  # type: ignore[attr-defined]
            else:
                pdf = pdfium.PdfDocument(source)  # type: ignore[attr-defined]
        except Exception as e:
            raise PDFParseError(f"Failed to open PDF: {e}") from e

        total_pages = len(pdf)
        logger.debug("PDF has %d pages", total_pages)

        # Determine which pages to process
        rng = page_range or PageRange()
        page_numbers = rng.select(total_pages)

        # Extract metadata via pypdf
        metadata = self._extract_metadata(source, total_pages)

        # Extract raw pages
        raw_pages: list[RawPage] = []
        for page_num in page_numbers:
            try:
                raw_page = self._extract_page(pdf, page_num)
                raw_pages.append(raw_page)
            except Exception as e:
                logger.warning("Failed to extract page %d: %s", page_num, e)

        pdf.close()
        logger.debug("Extracted %d raw pages", len(raw_pages))
        return raw_pages, metadata

    def _extract_page(self, pdf: Any, page_num: int) -> RawPage:
        """Extract text and spans from a single PDF page (1-indexed)."""

        page = pdf[page_num - 1]  # 0-indexed in pypdfium2

        # Get page dimensions
        width, height = page.get_size()

        # Extract text with position info
        page_text = page.get_textpage()
        spans = self._extract_spans(page_text, page_num, height)

        # Full text for fallback
        full_text = page_text.get_text_range() or ""

        page_ref = PageRef(number=page_num, width=width, height=height)
        return RawPage(page_ref=page_ref, spans=spans, raw_text=full_text)

    def _extract_spans(self, text_page: Any, page_num: int, page_height: float) -> list[RawTextSpan]:
        """Extract text spans with bounding boxes from a text page.

        Uses pypdfium2's text extraction API to get positioned text.
        Falls back to a single span if detailed extraction fails.
        """
        spans: list[RawTextSpan] = []

        try:
            # pypdfium2 get_text_range gives us the full text
            # For structured spans, we'd need count_chars + get_char_box
            # This is a best-effort approach
            text = text_page.get_text_range() or ""
            if not text.strip():
                return spans

            # Try to get character-level positions for span construction
            n_chars = text_page.count_chars()
            if n_chars == 0:
                # Single span fallback
                spans.append(RawTextSpan(
                    text=text.strip(),
                    font_size=12.0,
                    y0=page_height - 12,
                    y1=page_height,
                ))
                return spans

            # Group characters into spans by line
            current_text = ""
            current_y = 0.0
            current_x = 0.0
            current_size = 12.0

            for i in range(min(n_chars, len(text))):
                char = text[i] if i < len(text) else ""
                try:
                    char_box = text_page.get_char_box(i)
                    x0, y0, x1, y1 = char_box

                    if current_text and abs(y0 - current_y) > 3.0:
                        # New line — flush current span
                        spans.append(RawTextSpan(
                            text=current_text,
                            x0=current_x,
                            y0=current_y,
                            x1=x1,
                            y1=y1,
                            font_size=current_size,
                        ))
                        current_text = ""

                    if not current_text:
                        current_x = x0
                        current_y = y0

                    current_text += char

                    # Estimate font size from char height
                    char_height = abs(y1 - y0)
                    if char_height > 0:
                        current_size = char_height

                except Exception:
                    # If char-level extraction fails, just accumulate
                    current_text += char

            # Flush remaining
            if current_text:
                spans.append(RawTextSpan(
                    text=current_text,
                    x0=current_x,
                    y0=current_y,
                    font_size=current_size,
                ))

        except Exception as e:
            logger.debug("Detailed span extraction failed, using fallback: %s", e)
            text = text_page.get_text_range() or ""
            if text.strip():
                spans.append(RawTextSpan(text=text.strip(), font_size=12.0))

        return spans

    def _extract_metadata(self, source: str | bytes, total_pages: int) -> dict[str, Any]:
        """Extract PDF metadata using pypdf."""
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.debug("pypdf not available, skipping metadata extraction")
            return {"page_count": total_pages}

        try:
            if isinstance(source, bytes):
                import io

                reader = PdfReader(io.BytesIO(source))
            else:
                reader = PdfReader(str(source))

            meta: dict[str, Any] = {"page_count": len(reader.pages)}

            if reader.metadata:
                m = reader.metadata
                meta["title"] = str(m.title) if m.title else None
                meta["author"] = str(m.author) if m.author else None
                meta["subject"] = str(m.subject) if m.subject else None
                meta["creator"] = str(m.creator) if m.creator else None
                meta["producer"] = str(m.producer) if m.producer else None
                meta["creation_date"] = str(m.creation_date) if m.creation_date else None
                meta["mod_date"] = str(m.modification_date) if m.modification_date else None

            meta["encrypted"] = reader.is_encrypted
            return meta

        except Exception as e:
            logger.debug("Metadata extraction failed: %s", e)
            return {"page_count": total_pages}


def _describe_source(source: str | bytes) -> str:
    """Describe a source for logging (truncates bytes)."""
    if isinstance(source, bytes):
        return f"<bytes, {len(source)} bytes>"
    return str(Path(source).name)
