"""Image backend — renders PDF pages to PNG or JPG using pypdfium2.

This backend does NOT go through the IR pipeline. It uses pypdfium2's
native page rendering, which is fast and produces high-quality images
without requiring Poppler or any external system dependency.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pdf2any.errors import CapabilityError, PDFParseError, RenderError
from pdf2any.logging_config import get_logger
from pdf2any.renderers.base import Renderer
from pdf2any.utils.page_range import PageRange

if TYPE_CHECKING:
    from pdf2any.ir import IRDocument

logger = get_logger("backends.image")


class ImageBackend:
    """Render PDF pages to image files (PNG or JPG).

    Uses pypdfium2's native rendering — no Poppler required.

    Args:
        fmt: Output format — "png" or "jpg".
        dpi: Render resolution in DPI (default 150).
    """

    def __init__(self, fmt: str = "png", dpi: int = 150) -> None:
        self.fmt = fmt
        self.dpi = dpi

    def render_pages(
        self,
        pdf_path: str,
        output_pattern: str,
        *,
        page_range: PageRange | None = None,
    ) -> list[str]:
        """Render PDF pages to image files.

        Args:
            pdf_path: Path to the input PDF file.
            output_pattern: Output pattern with %d for page number,
                           e.g. "page-%d.png" or "output-%d.jpg".
            page_range: Optional page range to limit rendering.

        Returns:
            List of output file paths created.

        Raises:
            PDFParseError: If the PDF cannot be opened.
            RenderError: If rendering fails.
        """
        try:
            import pypdfium2 as pdfium  # type: ignore[import-untyped]
        except ImportError as e:
            raise PDFParseError(
                "pypdfium2 is required for image rendering. "
                "Install with: pip install pypdfium2"
            ) from e

        try:
            pdf = pdfium.PdfDocument(pdf_path)  # type: ignore[attr-defined]
        except Exception as e:
            raise PDFParseError(f"Failed to open PDF: {e}") from e

        total = len(pdf)
        rng = page_range or PageRange()
        page_numbers = rng.select(total)

        # Convert DPI to scale factor (PDF default is 72 DPI)
        scale = self.dpi / 72.0

        output_files: list[str] = []

        try:
            for page_num in page_numbers:
                page = pdf[page_num - 1]  # 0-indexed

                # Render the page to a bitmap
                bitmap = page.render(scale=scale)
                pil_image = bitmap.to_pil()

                # Generate output filename
                output_path = output_pattern % page_num
                if not output_path.endswith(f".{self.fmt}"):
                    output_path = f"{output_path}.{self.fmt}"

                # Save the image
                if self.fmt == "jpg":
                    # Convert to RGB for JPEG (no alpha channel)
                    if pil_image.mode in ("RGBA", "LA", "P"):
                        pil_image = pil_image.convert("RGB")
                    pil_image.save(output_path, "JPEG", quality=90)
                else:
                    pil_image.save(output_path, "PNG")

                output_files.append(output_path)
                logger.debug("Rendered page %d → %s", page_num, output_path)

        except Exception as e:
            raise RenderError(f"Image rendering failed: {e}") from e
        finally:
            pdf.close()

        return output_files


class ImageRendererPNG(Renderer):
    """Renderer adapter for PNG image output."""

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
        """PNG rendering requires the original PDF file path.

        Use the CLI which calls ImageBackend.render_pages() directly.
        """
        raise CapabilityError(
            "PNG output requires the original PDF file path. "
            "Use the CLI: pdf2any input.pdf -t png -o page-%d.png"
        )


class ImageRendererJPG(Renderer):
    """Renderer adapter for JPG image output."""

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
        """JPG rendering requires the original PDF file path.

        Use the CLI which calls ImageBackend.render_pages() directly.
        """
        raise CapabilityError(
            "JPG output requires the original PDF file path. "
            "Use the CLI: pdf2any input.pdf -t jpg -o page-%d.jpg"
        )
