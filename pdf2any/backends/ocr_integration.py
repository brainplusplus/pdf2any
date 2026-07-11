"""OCR integration — bridges PDFParser with OCR providers.

Two modes:
    - hybrid (default):  Use text layer if available, OCR only for pages
                         with little/no text (< MIN_TEXT_CHARS).
    - force:              OCR every page, ignore text layer entirely.

The hybrid approach handles mixed PDFs (some pages text-based, some scanned)
transparently — no user intervention needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pdf2any.errors import CapabilityError
from pdf2any.logging_config import get_logger
from pdf2any.models.page import PageRef
from pdf2any.parser.text_extractor import RawPage, RawTextSpan

if TYPE_CHECKING:
    from pdf2any.backends.ocr_provider import OCRProvider

logger = get_logger("ocr.integration")

# Pages with less than this many characters of text are considered "scanned"
# and will be OCR'd in hybrid mode.
MIN_TEXT_CHARS = 10


class OCRIntegration:
    """Manages OCR fallback/replace for PDF page text extraction.

    Args:
        provider: An OCRProvider instance.
        mode: 'hybrid' (OCR only for empty/scanned pages) or 'force' (OCR all).
        lang: Language code for OCR (e.g. 'eng', 'fra', 'ind').
        dpi: Render DPI for OCR (higher = more accurate, slower).
    """

    def __init__(
        self,
        provider: OCRProvider,
        *,
        mode: str = "hybrid",
        lang: str = "eng",
        dpi: int = 300,
    ) -> None:
        self.provider = provider
        self.mode = mode
        self.lang = lang
        self.dpi = dpi

    def should_ocr(self, raw_page: RawPage) -> bool:
        """Determine if a page needs OCR.

        In 'force' mode: always True.
        In 'hybrid' mode: True only if text layer is empty or near-empty.
        """
        if self.mode == "force":
            return True

        # Hybrid: check if text layer has meaningful content
        text = raw_page.raw_text.strip()
        if len(text) < MIN_TEXT_CHARS:
            logger.debug(
                "Page %d: text layer has %d chars — will OCR",
                raw_page.page_ref.number,
                len(text),
            )
            return True

        logger.debug(
            "Page %d: text layer has %d chars — skipping OCR",
            raw_page.page_ref.number,
            len(text),
        )
        return False

    def ocr_page(self, pdf_document: Any, page_num: int) -> RawPage:
        """Render a PDF page to image and run OCR.

        Args:
            pdf_document: pypdfium2 PdfDocument instance.
            page_num: 1-indexed page number.

        Returns:
            RawPage with OCR'd text.
        """
        page = pdf_document[page_num - 1]  # 0-indexed

        # Render page to image at specified DPI
        scale = self.dpi / 72.0
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()

        # Convert to PNG bytes
        import io

        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        # Run OCR
        logger.info("OCR: page %d (engine=%s, dpi=%d)", page_num, self.provider.name, self.dpi)
        text = self.provider.recognize(image_bytes, lang=self.lang)

        # Get page dimensions
        page_obj = page.get_page()
        width = float(page_obj.get_width())
        height = float(page_obj.get_height())

        # Create RawPage with OCR'd text as a single span
        page_ref = PageRef(number=page_num, width=width, height=height)
        span = RawTextSpan(
            text=text,
            x0=0,
            y0=0,
            x1=width,
            y1=height,
            font_size=12.0,  # Default — OCR can't detect font size
            font_name=None,
            bold=False,
            italic=False,
        )

        return RawPage(
            page_ref=page_ref,
            spans=[span],
            raw_text=text,
        )

    def process_page(
        self,
        pdf_document: Any,
        page_num: int,
        raw_page: RawPage | None = None,
    ) -> RawPage:
        """Process a single page — hybrid or force OCR.

        Args:
            pdf_document: pypdfium2 PdfDocument instance.
            page_num: 1-indexed page number.
            raw_page: Pre-extracted raw page (from text layer). None if not available.

        Returns:
            RawPage (either from text layer or OCR'd).
        """
        if raw_page and not self.should_ocr(raw_page):
            # Text layer is good enough — use it
            return raw_page

        # Need OCR
        try:
            return self.ocr_page(pdf_document, page_num)
        except CapabilityError:
            # OCR failed — fall back to text layer if available
            if raw_page:
                logger.warning(
                    "OCR failed for page %d — using text layer as fallback",
                    page_num,
                )
                return raw_page
            raise
