"""PDF metadata model.

Re-exports the IR's PDFMetadata to avoid duplication. The metadata is
extracted by the parser (via pypdf) and attached to the IRDocument.
"""

from __future__ import annotations

from pdf2any.ir import PDFMetadata

__all__ = ["PDFMetadata"]
