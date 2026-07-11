"""OCR provider registry — pluggable OCR engine selection.

Supported engines:
    - tesseract: Tesseract OCR via pytesseract (requires system Tesseract)
    - easyocr: EasyOCR (Python-native, GPU optional)
    - llm: LLM-based vision OCR (OpenAI GPT-4o, Gemini, etc.)

Usage:
    pdf2any scanned.pdf -t markdown --ocr
    pdf2any scanned.pdf -t markdown --ocr --ocr-engine tesseract
    pdf2any scanned.pdf -t markdown --ocr --ocr-engine easyocr
    pdf2any scanned.pdf -t markdown --ocr --ocr-engine llm --ocr-model gpt-4o
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pdf2any.errors import CapabilityError
from pdf2any.logging_config import get_logger

logger = get_logger("ocr")


class OCRProvider(ABC):
    """Abstract interface for OCR providers.

    A provider takes a rendered page image (PNG bytes) and returns
    extracted text.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g. 'tesseract', 'easyocr', 'llm')."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether this OCR provider is installed and ready."""

    @abstractmethod
    def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
        """Perform OCR on an image and return recognized text.

        Args:
            image_data: PNG image bytes (a rendered PDF page).
            lang: Language code for OCR (e.g. 'eng', 'fra', 'deu').

        Returns:
            Recognized text string.
        """

    def recognize_batch(
        self, images: list[bytes], *, lang: str = "eng"
    ) -> list[str]:
        """OCR multiple images. Default: sequential recognize().

        Override for batch-optimized providers (e.g. EasyOCR GPU batch).
        """
        return [self.recognize(img, lang=lang) for img in images]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[OCRProvider]] = {}


def register_provider(name: str, cls: type[OCRProvider]) -> None:
    """Register an OCR provider class."""
    _REGISTRY[name] = cls
    logger.debug("Registered OCR provider: %s", name)


def get_ocr_provider(
    engine: str = "auto",
    **kwargs: Any,
) -> OCRProvider:
    """Get an OCR provider by engine name.

    Args:
        engine: Provider name ('auto', 'tesseract', 'easyocr', 'llm').
                'auto' picks the first available provider.
        **kwargs: Provider-specific options (e.g. model='gpt-4o').

    Returns:
        An OCRProvider instance.

    Raises:
        CapabilityError: If no provider is available or the requested
                         engine is not installed.
    """
    if engine == "auto":
        # Try in priority order
        for name in ("tesseract", "easyocr", "llm"):
            if name in _REGISTRY:
                provider = _REGISTRY[name](**kwargs)
                if provider.is_available:
                    logger.info("Auto-selected OCR engine: %s", name)
                    return provider
        raise CapabilityError(
            "No OCR engine is available. Install one of:\n"
            "  pip install pdf2any[ocr-tesseract]  (Tesseract — also needs system Tesseract)\n"
            "  pip install pdf2any[ocr-easyocr]    (EasyOCR — Python-native)\n"
            "  pip install pdf2any[ocr-llm]        (LLM vision — needs API key)"
        )

    if engine not in _REGISTRY:
        raise CapabilityError(
            f"Unknown OCR engine '{engine}'. Available: {', '.join(_REGISTRY.keys()) or 'none'}"
        )

    provider = _REGISTRY[engine](**kwargs)
    if not provider.is_available:
        raise CapabilityError(
            f"OCR engine '{engine}' is not available. "
            f"Make sure it is installed and configured."
        )
    return provider


def list_available_engines() -> list[str]:
    """List all registered OCR engine names."""
    return list(_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Auto-register providers (each provider registers itself on import)
# ---------------------------------------------------------------------------

def _autoregister() -> None:
    """Try importing and registering all built-in providers."""
    try:
        from pdf2any.backends.ocr_tesseract import TesseractProvider

        register_provider("tesseract", TesseractProvider)
    except ImportError:
        logger.debug("Tesseract provider not available (install pytesseract)")

    try:
        from pdf2any.backends.ocr_easyocr import EasyOCRProvider

        register_provider("easyocr", EasyOCRProvider)
    except ImportError:
        logger.debug("EasyOCR provider not available (install easyocr)")

    try:
        from pdf2any.backends.ocr_llm import LLMOCRProvider

        register_provider("llm", LLMOCRProvider)
    except ImportError:
        logger.debug("LLM OCR provider not available (install openai or google-generativeai)")


_autoregister()
