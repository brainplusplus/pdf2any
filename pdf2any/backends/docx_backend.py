"""DOCX backend — isolated from the IR renderer architecture.

Uses pdf2docx as the dedicated DOCX conversion engine. This backend
does NOT go through the IR pipeline; it delegates directly to pdf2docx
which has its own PDF-to-DOCX conversion logic.

This isolation is intentional: pdf2docx has specialized layout recovery
that produces better DOCX output than rendering from our semantic IR.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pdf2any.errors import CapabilityError, RenderError
from pdf2any.logging_config import get_logger
from pdf2any.renderers.base import Renderer
from pdf2any.utils.page_range import PageRange

if TYPE_CHECKING:
    from pdf2any.ir import IRDocument

logger = get_logger("backends.docx")


class DOCXBackend:
    """DOCX conversion backend using pdf2docx.

    This is NOT an IR-based renderer. It delegates to pdf2docx.Converter
    which performs its own PDF layout analysis and DOCX reconstruction.
    """

    def convert(
        self,
        pdf_path: str,
        output_path: str,
        *,
        page_range: PageRange | None = None,
    ) -> None:
        """Convert a PDF file to DOCX.

        Args:
            pdf_path: Path to the input PDF file.
            output_path: Path for the output DOCX file.
            page_range: Optional page range to limit conversion.

        Raises:
            CapabilityError: If pdf2docx is not installed.
            RenderError: If conversion fails.
        """
        try:
            from pdf2docx import Converter  # type: ignore[import-untyped]
        except ImportError as e:
            raise CapabilityError(
                "DOCX output requires pdf2docx. "
                "Install with: pip install pdf2any[docx]"
            ) from e

        logger.debug("Converting %s → %s (DOCX)", pdf_path, output_path)

        try:
            cv = Converter(pdf_path)

            # Determine page range for pdf2docx
            if page_range and page_range.pages:
                # pdf2docx uses 0-indexed page ranges
                pages = [p - 1 for p in page_range.pages]
                cv.convert(output_path, pages=pages)
            else:
                cv.convert(output_path)

            cv.close()
            logger.debug("DOCX conversion complete: %s", output_path)

        except CapabilityError:
            raise
        except Exception as e:
            raise RenderError(f"DOCX conversion failed: {e}") from e


class DOCXRenderer(Renderer):
    """Renderer adapter for the DOCX backend.

    The registry uses this to provide a uniform Renderer interface.
    Since DOCX conversion doesn't use IR, this adapter accepts an
    IRDocument but delegates to pdf2docx using the original PDF path
    (stored in the IR metadata or passed via context).

    Note: For DOCX, the CLI should use DOCXBackend.convert() directly
    rather than going through this renderer, as it needs the original
    PDF file path.
    """

    @property
    def is_binary(self) -> bool:
        return True

    def render(
        self,
        doc: IRDocument,
        *,
        standalone: bool = False,
        pretty: bool = False,
    ) -> bytes:
        """Render is not supported for DOCX via IR.

        DOCX requires the original PDF file path. Use DOCXBackend.convert()
        directly from the CLI.
        """
        raise CapabilityError(
            "DOCX output requires the original PDF file path. "
            "Use the CLI: pdf2any input.pdf -t docx -o output.docx"
        )
