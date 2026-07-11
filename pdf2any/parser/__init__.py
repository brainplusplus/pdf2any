"""PDF parsing and extraction stage.

Reads PDF via pypdfium2 (primary engine) + pypdf (metadata), extracts
text and layout information, and optionally uses pdfplumber for table
extraction.
"""

from pdf2any.parser.pdf_parser import PDFParser

__all__ = ["PDFParser"]
