"""OCR provider — abstract interface for future OCR integration.

In v1, ``--ocr`` is an experimental flag that exits with a CapabilityError.
This module defines the interface that future OCR providers (Tesseract,
EasyOCR, Surya) will implement.

Future roadmap:
    - v0.2: Tesseract provider via pytesseract (requires system Tesseract)
    - v0.3: EasyOCR provider (Python-native, no system dep)
    - v0.4: Pluggable OCR provider registry
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pdf2any.errors import CapabilityError


class OCRProvider(ABC):
    """Abstract interface for OCR providers.

    A provider takes a rendered page image and returns extracted text.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g. 'tesseract', 'easyocr')."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether this OCR provider is installed and ready."""

    @abstractmethod
    def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
        """Perform OCR on an image and return recognized text.

        Args:
            image_data: PNG/JPG image bytes (a rendered PDF page).
            lang: Language code for OCR (e.g. 'eng', 'fra', 'deu').

        Returns:
            Recognized text string.
        """


class NoOCRProvider(OCRProvider):
    """Default stub provider — OCR not implemented in v1.

    Calling ``recognize()`` raises CapabilityError so the CLI can exit
    with code 3 and a clear message.
    """

    @property
    def name(self) -> str:
        return "none"

    @property
    def is_available(self) -> bool:
        return False

    def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
        raise CapabilityError(
            "OCR is not yet implemented in pdf2any v0.1. "
            "Tesseract OCR support is planned for v0.2. "
            "Track progress: https://github.com/pdf2any/pdf2any/issues"
        )


# Default provider — always the stub in v1
_default_provider: OCRProvider = NoOCRProvider()


def get_ocr_provider() -> OCRProvider:
    """Get the current OCR provider (stub in v1)."""
    return _default_provider


def set_ocr_provider(provider: OCRProvider) -> None:
    """Set a custom OCR provider (for future use)."""
    global _default_provider
    _default_provider = provider
