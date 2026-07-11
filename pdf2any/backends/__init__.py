"""Backends — non-IR-based output paths.

DOCX: delegates to pdf2docx (isolated from IR renderer architecture).
Image: uses pypdfium2 native page rendering.
OCR: stub interface for future implementation.
"""

__all__ = ["DOCXBackend", "ImageBackend", "OCRProvider"]
