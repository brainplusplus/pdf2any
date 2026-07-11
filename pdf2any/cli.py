"""pdf2any CLI — Pandoc-style command-line interface for semantic PDF conversion.

Usage examples:
    pdf2any input.pdf -t markdown -o out.md
    pdf2any input.pdf -t html -o out.html --standalone
    pdf2any input.pdf -t prosemirror -o out.json
    pdf2any input.pdf -t docx -o out.docx
    pdf2any input.pdf -t png --pages 1-3 -o page-%d.png
    pdf2any --list-output-formats
    pdf2any --version
    cat input.pdf | pdf2any -t markdown > out.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

from pdf2any import __version__
from pdf2any.errors import CapabilityError, PDF2AnyError, UsageError
from pdf2any.logging_config import configure_logging, get_logger
from pdf2any.normalize.normalizer import SemanticNormalizer
from pdf2any.parser.pdf_parser import PDFParser
from pdf2any.registry import create_default_registry
from pdf2any.utils.io_utils import read_input_source, write_output
from pdf2any.utils.page_range import PageRange, parse_page_range

logger = get_logger("cli")


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse argument parser."""
    parser = argparse.ArgumentParser(
        prog="pdf2any",
        description=(
            "Pandoc-style CLI for semantic PDF conversion. "
            "Convert PDF to Markdown, HTML, ProseMirror JSON, DOCX, and more."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  pdf2any input.pdf -t markdown -o out.md\n"
            "  pdf2any input.pdf -t html -o out.html --standalone\n"
            "  pdf2any input.pdf -t prosemirror -o out.json\n"
            "  pdf2any input.pdf -t docx -o out.docx\n"
            "  pdf2any input.pdf -t json -o out.ir.json\n"
            "  cat input.pdf | pdf2any -t markdown > out.md\n"
            "  pdf2any --list-output-formats\n"
            "\n"
            "Note: PDF is presentation-oriented. Semantic recovery is heuristic.\n"
        ),
    )

    # Positional input (optional — stdin if omitted)
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Input PDF file path. If omitted, reads from stdin.",
    )

    # Format flags
    parser.add_argument(
        "-f", "--from",
        dest="from_format",
        default="pdf",
        help="Input format (default: pdf). Currently only pdf is supported.",
    )
    parser.add_argument(
        "-t", "--to",
        dest="to_format",
        default=None,
        help="Output format: markdown, html, docx, prosemirror, json, txt, png, jpg.",
    )

    # Output
    parser.add_argument(
        "-o", "--output",
        dest="output",
        default=None,
        help="Output file path. If omitted, text output goes to stdout.",
    )

    # Page selection
    parser.add_argument(
        "--pages",
        default=None,
        help="Page range, e.g. '1-3,5,7-9'. Pages are 1-indexed.",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Start page (1-indexed).",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=None,
        help="End page (1-indexed).",
    )

    # Processing options
    parser.add_argument(
        "--ocr",
        action="store_true",
        default=False,
        help="Enable OCR (hybrid mode — OCR only for scanned pages).",
    )
    parser.add_argument(
        "--ocr-force",
        dest="ocr_force",
        action="store_true",
        default=False,
        help="Force OCR on all pages, ignoring text layer (implies --ocr).",
    )
    parser.add_argument(
        "--ocr-engine",
        dest="ocr_engine",
        default="auto",
        help="OCR engine: auto, tesseract, easyocr, llm (default: auto).",
    )
    parser.add_argument(
        "--ocr-provider",
        dest="ocr_provider",
        default="openai",
        help="LLM provider for --ocr-engine llm: openai, anthropic, gemini (default: openai).",
    )
    parser.add_argument(
        "--ocr-model",
        dest="ocr_model",
        default=None,
        help="Model name for LLM OCR (e.g. gpt-4o, claude-sonnet-4-20250514, gemini-2.5-flash).",
    )
    parser.add_argument(
        "--ocr-lang",
        dest="ocr_lang",
        default="eng",
        help="OCR language code (default: eng). Examples: eng, fra, deu, ind, ch_sim.",
    )
    parser.add_argument(
        "--ocr-base-url",
        dest="ocr_base_url",
        default=None,
        help="Custom API base URL for LLM OCR (OpenAI-compatible: OpenRouter, Groq, Ollama).",
    )
    parser.add_argument(
        "--ocr-concurrency",
        dest="ocr_concurrency",
        type=int,
        default=1,
        help="Parallel OCR calls for LLM engine (default: 1).",
    )
    parser.add_argument(
        "--ocr-dpi",
        dest="ocr_dpi",
        type=int,
        default=300,
        help="Render DPI for OCR (default: 300). Higher = more accurate, slower.",
    )
    parser.add_argument(
        "--extract-images",
        dest="extract_images",
        action="store_true",
        default=False,
        help="Extract embedded images from the PDF.",
    )

    # Output formatting
    parser.add_argument(
        "--standalone",
        action="store_true",
        default=False,
        help="Produce a standalone document (e.g. full HTML with <html> wrapper).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=False,
        help="Pretty-print output (indent JSON/HTML).",
    )
    parser.add_argument(
        "--json",
        dest="json_mode",
        action="store_true",
        default=False,
        help="Emit machine-readable metadata JSON to stdout instead of converted output.",
    )

    # Debug
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable verbose debug logging to stderr.",
    )

    # Information flags
    parser.add_argument(
        "--list-input-formats",
        dest="list_input_formats",
        action="store_true",
        default=False,
        help="List supported input formats and exit.",
    )
    parser.add_argument(
        "--list-output-formats",
        dest="list_output_formats",
        action="store_true",
        default=False,
        help="List supported output formats and exit.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pdf2any {__version__}",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code: 0 success, 1 conversion error, 2 usage error,
                   3 capability error.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(debug=args.debug)

    # Handle info-only flags
    if args.list_input_formats:
        registry = create_default_registry()
        for fmt in registry.list_inputs():
            print(fmt)
        return 0

    if args.list_output_formats:
        registry = create_default_registry()
        for info in registry.list_outputs():
            binary_tag = " (binary)" if info.binary else ""
            print(f"{info.name:15s}  {info.description}{binary_tag}")
        return 0

    # Validate required args
    if args.to_format is None:
        print("Error: -t/--to is required (or use --list-output-formats)", file=sys.stderr)
        print("Use --help for usage information.", file=sys.stderr)
        return 2

    registry = create_default_registry()

    # Validate input format
    if args.from_format not in registry.list_inputs():
        print(f"Error: unsupported input format '{args.from_format}'", file=sys.stderr)
        print(f"Supported: {', '.join(registry.list_inputs())}", file=sys.stderr)
        return 2

    # Validate output format
    if not registry.is_registered(args.to_format):
        print(f"Error: unsupported output format '{args.to_format}'", file=sys.stderr)
        print(f"Supported: {', '.join(registry.output_names())}", file=sys.stderr)
        return 2

    # Check binary output requires -o
    format_info = registry.get(args.to_format)
    if format_info.binary and args.output is None:
        print(
            f"Error: -o/--output is required for binary format '{args.to_format}'",
            file=sys.stderr,
        )
        return 2

    # OCR setup
    ocr_integration = None
    if args.ocr or args.ocr_force:
        from pdf2any.backends.ocr_integration import OCRIntegration
        from pdf2any.backends.ocr_provider import get_ocr_provider

        ocr_mode = "force" if args.ocr_force else "hybrid"

        provider_kwargs = {}
        if args.ocr_engine == "llm":
            provider_kwargs["provider"] = args.ocr_provider
            if args.ocr_model:
                provider_kwargs["model"] = args.ocr_model
            if args.ocr_base_url:
                provider_kwargs["base_url"] = args.ocr_base_url
            provider_kwargs["concurrency"] = args.ocr_concurrency

        try:
            provider = get_ocr_provider(args.ocr_engine, **provider_kwargs)
            ocr_integration = OCRIntegration(
                provider=provider,
                mode=ocr_mode,
                lang=args.ocr_lang,
                dpi=args.ocr_dpi,
            )
            logger.info(
                "OCR enabled: engine=%s, mode=%s, lang=%s, dpi=%d",
                provider.name,
                ocr_mode,
                args.ocr_lang,
                args.ocr_dpi,
            )
        except CapabilityError as e:
            if args.json_mode:
                _emit_json_error(args, e)
            else:
                print(f"Error: {e.message}", file=sys.stderr)
            return e.exit_code

    # Start conversion
    start_time = time.monotonic()

    try:
        result = _run_conversion(args, registry, ocr_integration)
        duration_ms = int((time.monotonic() - start_time) * 1000)

        if args.json_mode:
            _emit_json_success(args, result, duration_ms)
        else:
            write_output(result["content"], args.output)

        return 0

    except PDF2AnyError as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.debug("Conversion failed after %dms: %s", duration_ms, e)
        if args.json_mode:
            _emit_json_error(args, e, duration_ms)
        else:
            print(f"Error: {e.message}", file=sys.stderr)
        return e.exit_code

    except Exception as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.exception("Unexpected error during conversion")
        error = PDF2AnyError(f"Unexpected error: {e}")
        if args.json_mode:
            _emit_json_error(args, error, duration_ms)
        else:
            print(f"Error: {e}", file=sys.stderr)
        return error.exit_code


def _run_conversion(args: argparse.Namespace, registry: Any, ocr_integration: Any = None) -> dict[str, Any]:
    """Run the actual conversion and return result dict.

    Returns:
        Dict with keys: content, pages_processed, output_format, warnings.
    """
    # Parse page range
    page_range = parse_page_range(args.pages, args.start, args.end)

    # Read input
    data, source_label = read_input_source(args.input)
    logger.debug("Read input from %s (%d bytes)", source_label, len(data))

    format_info = registry.get(args.to_format)
    to_format = args.to_format

    # Handle binary backends specially
    if to_format == "docx":
        return _convert_docx(args, page_range, source_label)
    elif to_format in ("png", "jpg"):
        return _convert_images(args, page_range, source_label, to_format)

    # Text-based formats: go through IR pipeline
    # Parse PDF
    parser = PDFParser(
        enable_tables=True,
        ocr_integration=ocr_integration,
    )
    raw_pages, metadata = parser.parse(data, page_range)
    logger.debug("Parsed %d pages", len(raw_pages))

    # Normalize to IR
    normalizer = SemanticNormalizer(enable_tables=True)
    ir_doc = normalizer.normalize(
        raw_pages,
        metadata,
        pdf_source=data if args.input is None else args.input,
        page_range=page_range.pages if page_range.explicit else None,
    )

    # Render
    renderer = format_info.renderer_cls()
    content = renderer.render(
        ir_doc,
        standalone=args.standalone,
        pretty=args.pretty,
    )

    return {
        "content": content,
        "pages_processed": len(raw_pages),
        "output_format": to_format,
        "warnings": [],
    }


def _convert_docx(
    args: argparse.Namespace,
    page_range: PageRange,
    source_label: str,
) -> dict[str, Any]:
    """Convert to DOCX using the isolated pdf2docx backend."""
    if args.input is None:
        raise UsageError("DOCX output requires a file path input (not stdin).")

    from pdf2any.backends.docx_backend import DOCXBackend

    backend = DOCXBackend()
    backend.convert(args.input, args.output, page_range=page_range)

    return {
        "content": b"",  # Written directly to file
        "pages_processed": 0,
        "output_format": "docx",
        "warnings": [],
    }


def _convert_images(
    args: argparse.Namespace,
    page_range: PageRange,
    source_label: str,
    fmt: str,
) -> dict[str, Any]:
    """Convert to PNG/JPG using the image backend."""
    if args.input is None:
        raise UsageError(f"{fmt.upper()} output requires a file path input (not stdin).")

    from pdf2any.backends.image_backend import ImageBackend

    backend = ImageBackend(fmt=fmt, dpi=150)
    output_files = backend.render_pages(
        args.input,
        args.output,
        page_range=page_range,
    )

    return {
        "content": b"",  # Written directly to files
        "pages_processed": len(output_files),
        "output_format": fmt,
        "warnings": [],
    }


def _emit_json_success(
    args: argparse.Namespace,
    result: dict[str, Any],
    duration_ms: int,
) -> None:
    """Emit success metadata as JSON to stdout."""
    payload = {
        "ok": True,
        "input": args.input or "<stdin>",
        "output_format": result["output_format"],
        "output_path": args.output,
        "pages_processed": result["pages_processed"],
        "duration_ms": duration_ms,
        "ir_version": "1.0",
        "pdf2any_version": __version__,
        "warnings": result.get("warnings", []),
        "error": None,
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))


def _emit_json_error(
    args: argparse.Namespace,
    error: PDF2AnyError,
    duration_ms: int = 0,
) -> None:
    """Emit error metadata as JSON to stdout."""
    info = error.to_info()
    payload = {
        "ok": False,
        "input": args.input or "<stdin>",
        "output_format": args.to_format,
        "output_path": args.output,
        "pages_processed": 0,
        "duration_ms": duration_ms,
        "ir_version": "1.0",
        "pdf2any_version": __version__,
        "warnings": [],
        "error": {
            "code": info.code,
            "message": info.message,
            "type": info.type,
        },
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
