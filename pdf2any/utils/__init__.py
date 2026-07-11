"""Cross-cutting utilities for pdf2any."""

from pdf2any.utils.io_utils import read_input_source, write_output
from pdf2any.utils.page_range import PageRange, parse_page_range
from pdf2any.utils.platform_info import get_artifact_name, get_platform_id

__all__ = [
    "PageRange",
    "get_artifact_name",
    "get_platform_id",
    "parse_page_range",
    "read_input_source",
    "write_output",
]
