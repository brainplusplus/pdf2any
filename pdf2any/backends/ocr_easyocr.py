"""EasyOCR provider — Python-native OCR, GPU optional.

Requirements:
    pip install pdf2any[ocr-easyocr]

EasyOCR supports 80+ languages and runs on CPU or GPU (CUDA).
First run downloads model weights (~100MB per language).
"""

from __future__ import annotations

import io
from typing import Any

from pdf2any.backends.ocr_provider import OCRProvider, register_provider
from pdf2any.errors import CapabilityError
from pdf2any.logging_config import get_logger

logger = get_logger("ocr.easyocr")


class EasyOCRProvider(OCRProvider):
    """EasyOCR — Python-native, no system binary needed.

    Supports GPU (CUDA) if available, falls back to CPU.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._reader: Any = None
        self._gpu: bool = kwargs.get("gpu")  # None = auto-detect
        self._lang_map: dict[str, list[str]] = {
            "en": ["en"],
            "eng": ["en"],
            "fr": ["fr"],
            "fra": ["fr"],
            "de": ["de"],
            "deu": ["de"],
            "id": ["id"],
            "ind": ["id"],
            "zh": ["ch_sim"],
            "ja": ["ja"],
            "ko": ["ko"],
            "ar": ["ar"],
        }

    @property
    def name(self) -> str:
        return "easyocr"

    @property
    def is_available(self) -> bool:
        """Check if easyocr is importable."""
        try:
            import easyocr  # type: ignore[import-untyped]  # noqa: F401
            return True
        except ImportError:
            return False

    def _get_reader(self, lang: str = "eng") -> Any:
        """Lazily initialize EasyOCR Reader (expensive — loads model)."""
        if self._reader is not None:
            return self._reader

        import easyocr  # type: ignore[import-untyped]

        langs = self._lang_map.get(lang, ["en"])
        gpu = self._gpu
        if gpu is None:
            # Auto-detect CUDA
            try:
                import torch  # type: ignore[import-untyped]
                gpu = torch.cuda.is_available()
            except ImportError:
                gpu = False

        logger.info("EasyOCR: initializing reader (langs=%s, gpu=%s)", langs, gpu)
        self._reader = easyocr.Reader(langs, gpu=gpu)
        return self._reader

    def recognize(self, image_data: bytes, *, lang: str = "eng") -> str:
        """Run EasyOCR on a PNG image.

        Args:
            image_data: PNG image bytes.
            lang: Language code (e.g. 'eng', 'fra', 'ind').

        Returns:
            Recognized text string.
        """
        if not self.is_available:
            raise CapabilityError(
                "EasyOCR is not available. Install with: pip install easyocr"
            )

        import numpy as np  # type: ignore[import-untyped]
        from PIL import Image  # type: ignore[import-untyped]

        try:
            reader = self._get_reader(lang)
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)

            # EasyOCR returns list of (bbox, text, confidence)
            results = reader.readtext(image_array)

            # Sort by vertical position (top to bottom), then horizontal
            # Each result: ([top_left, top_right, bottom_right, bottom_left], text, conf)
            results.sort(key=lambda r: (r[0][0][1], r[0][0][0]))

            lines = [text for _, text, _ in results]
            text = "\n".join(lines)
            logger.debug("EasyOCR: %d chars from %d regions", len(text), len(results))
            return text.strip()
        except Exception as e:
            raise CapabilityError(f"EasyOCR failed: {e}") from e

    def recognize_batch(
        self, images: list[bytes], *, lang: str = "eng"
    ) -> list[str]:
        """EasyOCR can batch images on GPU for better throughput."""
        if not self.is_available:
            raise CapabilityError(
                "EasyOCR is not available. Install with: pip install easyocr"
            )

        # For CPU or small batches, sequential is fine
        if len(images) <= 1:
            return [self.recognize(img, lang=lang) for img in images]

        # GPU batch mode
        import numpy as np  # type: ignore[import-untyped]
        from PIL import Image  # type: ignore[import-untyped]

        try:
            reader = self._get_reader(lang)
            image_arrays = [np.array(Image.open(io.BytesIO(img))) for img in images]

            results_batch = reader.readtext_batched(image_arrays)

            texts = []
            for results in results_batch:
                results = sorted(
                    results, key=lambda r: (r[0][0][1], r[0][0][0])
                )
                lines = [text for _, text, _ in results]
                texts.append("\n".join(lines).strip())

            return texts
        except Exception as e:
            # Fallback to sequential on batch error
            logger.warning("EasyOCR batch failed, falling back to sequential: %s", e)
            return [self.recognize(img, lang=lang) for img in images]


register_provider("easyocr", EasyOCRProvider)
