"""Tests for the CLI."""

from __future__ import annotations

import json
import sys
from unittest.mock import patch

import pytest

from pdf2any.cli import build_parser, main


class TestCLIParser:
    """Tests for argparse configuration."""

    def test_build_parser(self):
        parser = build_parser()
        assert parser.prog == "pdf2any"

    def test_version_flag(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_help_flag(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--help"])

    def test_input_positional(self):
        parser = build_parser()
        args = parser.parse_args(["input.pdf", "-t", "markdown"])
        assert args.input == "input.pdf"
        assert args.to_format == "markdown"

    def test_no_input_defaults_to_none(self):
        parser = build_parser()
        args = parser.parse_args(["-t", "markdown"])
        assert args.input is None

    def test_defaults(self):
        parser = build_parser()
        args = parser.parse_args(["file.pdf", "-t", "txt"])
        assert args.from_format == "pdf"
        assert args.output is None
        assert args.standalone is False
        assert args.pretty is False
        assert args.json_mode is False
        assert args.debug is False


class TestCLIInfoFlags:
    """Tests for --list-* and info flags."""

    def test_list_output_formats(self, capsys):
        rc = main(["--list-output-formats"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "markdown" in captured.out
        assert "html" in captured.out
        assert "prosemirror" in captured.out
        assert "docx" in captured.out

    def test_list_input_formats(self, capsys):
        rc = main(["--list-input-formats"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "pdf" in captured.out

    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0


class TestCLIErrors:
    """Tests for CLI error handling."""

    def test_missing_to_format(self, capsys):
        rc = main(["input.pdf"])
        assert rc == 2  # Usage error

    def test_invalid_output_format(self, capsys):
        rc = main(["input.pdf", "-t", "nonexistent"])
        assert rc == 2

    def test_binary_format_without_output(self, capsys):
        rc = main(["input.pdf", "-t", "docx"])
        assert rc == 2

    def test_png_without_output(self, capsys):
        rc = main(["input.pdf", "-t", "png"])
        assert rc == 2

    def test_ocr_no_engine_available(self, capsys):
        """--ocr without any OCR engine installed should give capability error."""
        rc = main(["input.pdf", "-t", "markdown", "--ocr"])
        # If no OCR engine is installed → exit 3 (capability error)
        # If an engine IS installed → will try to parse → exit 1 (file not found)
        assert rc in (1, 3)

    def test_ocr_force_implies_ocr(self, capsys):
        """--ocr-force should enable OCR without needing --ocr."""
        rc = main(["input.pdf", "-t", "markdown", "--ocr-force"])
        assert rc in (1, 3)


class TestCLIJSONMode:
    """Tests for --json machine-readable output."""

    def test_json_error_output(self, capsys):
        """--json mode should emit JSON even on error."""
        rc = main(["nonexistent.pdf", "-t", "markdown", "--json"])
        assert rc != 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["ok"] is False
        assert data["error"]["code"] is not None
        assert data["pdf2any_version"] is not None

    def test_ocr_json_error(self, capsys):
        """OCR capability error in JSON mode."""
        rc = main(["input.pdf", "-t", "markdown", "--ocr", "--json"])
        assert rc in (1, 3)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["ok"] is False
        assert data["error"]["type"] == "CapabilityError"
