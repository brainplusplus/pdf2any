"""Tesseract OCR provider — uses pytesseract + system Tesseract.

Requirements:
    pip install pdf2any[ocr-tesseract]
    # Also install Tesseract system binary:
    #   Ubuntu/Debian: sudo apt install tesseract-ocr
    #   macOS:         brew install tesseract
    #   Windows:       https://github.com/UB-Mannheim/tesseract/wiki
"""

from __future__ import annotations

import io
import shutil
from typing import Any

from pdf2any.backends.ocr_provider import OCRProvider, register_provider
from pdf2any.errors import CapabilityError
from pdf2any.logging_config import get_logger

logger = get_logger("ocr.tesseract")


class TesseractProvider(OCRProvider):
    """Tesseract OCR via pytesseract.

    Requires both the pytesseract Python package AND the Tesseract
    system binary on PATH.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._pytesseract: Any = None
        self._tesseract_cmd: str = kwargs.get(
            "tesseract_cmd", shutil.which("tesseract") or ""
        )

    @property
    def name(self) -> str:
        return "tesseract"

    @property
    def is_available(self) -> bool:
        """Check if pytesseract is importable AND tesseract binary exists."""
        try:
            import pytesseract  # type: ignore[import-untyped]
            self._pytesseract = pytesseract
        except ImportError:
            return False

        if not self._tesseract_cmd:
            # Try default PATH lookup
            self._tesseract_cmd = shutil.which("tesseract") or ""

        return bool(self._tesseract_cmd)

    def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
        """Run Tesseract OCR on a PNG image.

        Args:
            image_data: PNG image bytes.
            lang: Tesseract language code (e.g. 'eng', 'fra', 'ind', 'deu').

        Returns:
            Recognized text string.
        """
        if not self.is_available:
            raise CapabilityError(
                "Tesseract is not available. Install with: "
                "pip install pytesseract && apt install tesseract-ocr"
            )

        from PIL import Image  # type: ignore[import-untyped]

        try:
            image = Image.open(io.BytesIO(image_data))
            text = self._pytesseract.image_to_string(image, lang=lang)
            logger.debug("Tesseract OCR: %d chars from image", len(text))
            return text.strip()
        except Exception as e:
            raise CapabilityError(f"Tesseract OCR failed: {e}") from e

    def recognize_batch(
        self, images: list[bytes], *, lang: str = "eng"
    ) -> list[str]:
        """Process images sequentially (Tesseract is single-image)."""
        return [self.recognize(img, lang=lang) for img in images]


register_provider("tesseract", TesseractProvider)
