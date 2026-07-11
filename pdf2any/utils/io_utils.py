"""I/O utilities — stdin reading, file writing, binary/text output routing."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def read_input_source(input_path: str | None) -> tuple[bytes | str, str]:
    """Read the input PDF from a file path or stdin.

    Args:
        input_path: Path to the PDF file. If None, reads from stdin.

    Returns:
        Tuple of (data, source_label) where data is the raw bytes
        and source_label is a human-readable identifier for error messages.

    Raises:
        FileNotFoundError: If input_path doesn't exist.
        OSError: If reading fails.
    """
    if input_path is None:
        # Read binary from stdin
        data = sys.stdin.buffer.read()
        return data, "<stdin>"

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    data = path.read_bytes()
    return data, str(path)


def write_output(content: str | bytes, output_path: str | None) -> None:
    """Write output to a file or stdout.

    Args:
        content: The rendered content (str for text formats, bytes for binary).
        output_path: File path to write to. If None, writes to stdout.
    """
    if output_path is None:
        # Write to stdout
        if isinstance(content, bytes):
            sys.stdout.buffer.write(content)
            sys.stdout.buffer.flush()
        else:
            print(content)
        return

    path = Path(output_path)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def needs_output_file(output_format: str) -> bool:
    """Whether the given output format requires -o (binary formats)."""
    return output_format in ("docx", "png", "jpg")
