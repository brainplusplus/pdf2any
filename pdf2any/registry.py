"""Format registry — maps output format names to renderers and backends.

This is the central dispatch table the CLI uses to route ``-t <format>``
to the correct renderer or backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(slots=True, frozen=True)
class FormatInfo:
    """Describes a registered output format."""

    name: str
    description: str
    binary: bool  # True for docx/png/jpg; False for text-based formats
    renderer_cls: type  # type: ignore[type-arg]
    standalone_supported: bool = True  # --standalone flag relevant (HTML)
    notes: str = ""


class FormatRegistry:
    """Central registry for input and output formats.

    Usage::

        registry = FormatRegistry()
        registry.register_output("markdown", MarkdownRenderer, binary=False, ...)
        info = registry.get("markdown")
        renderer = info.renderer_cls()
        output = renderer.render(doc)
    """

    def __init__(self) -> None:
        self._outputs: dict[str, FormatInfo] = {}
        self._inputs: set[str] = set()

    # --- Input formats -------------------------------------------------

    def register_input(self, name: str) -> None:
        self._inputs.add(name)

    def list_inputs(self) -> list[str]:
        return sorted(self._inputs)

    # --- Output formats ------------------------------------------------

    def register_output(
        self,
        name: str,
        renderer_cls: type,  # type: ignore[type-arg]
        *,
        binary: bool = False,
        description: str = "",
        standalone_supported: bool = True,
        notes: str = "",
    ) -> None:
        self._outputs[name] = FormatInfo(
            name=name,
            description=description,
            binary=binary,
            renderer_cls=renderer_cls,
            standalone_supported=standalone_supported,
            notes=notes,
        )

    def get(self, name: str) -> FormatInfo:
        """Get format info by name. Raises KeyError if not registered."""
        if name not in self._outputs:
            raise KeyError(
                f"Unknown output format: '{name}'. "
                f"Available: {', '.join(sorted(self._outputs))}. "
                f"Use --list-output-formats to see all options."
            )
        return self._outputs[name]

    def is_registered(self, name: str) -> bool:
        return name in self._outputs

    def is_binary(self, name: str) -> bool:
        return self.get(name).binary

    def list_outputs(self) -> list[FormatInfo]:
        return sorted(self._outputs.values(), key=lambda f: f.name)

    def output_names(self) -> list[str]:
        return sorted(self._outputs)


def create_default_registry() -> FormatRegistry:
    """Create and populate the default registry with all built-in formats.

    Imports are lazy to keep startup fast and avoid importing optional
    dependencies (pdf2docx, pdfplumber) when they're not needed.
    """
    from pdf2any.renderers.html_renderer import HTMLRenderer
    from pdf2any.renderers.json_renderer import JSONRenderer
    from pdf2any.renderers.markdown_renderer import MarkdownRenderer
    from pdf2any.renderers.prosemirror_renderer import ProseMirrorRenderer
    from pdf2any.renderers.text_renderer import TextRenderer

    registry = FormatRegistry()

    # Input formats
    registry.register_input("pdf")

    # Text-based renderers (IR → text)
    registry.register_output(
        "markdown",
        MarkdownRenderer,
        binary=False,
        description="Semantic Markdown",
        notes="Best-effort semantic markdown with headings, lists, tables, images.",
    )
    registry.register_output(
        "html",
        HTMLRenderer,
        binary=False,
        description="HTML fragment (use --standalone for full document)",
        standalone_supported=True,
    )
    registry.register_output(
        "prosemirror",
        ProseMirrorRenderer,
        binary=False,
        description="ProseMirror JSON",
        notes='Root node: {"type": "doc", "content": [...]}',
    )
    registry.register_output(
        "json",
        JSONRenderer,
        binary=False,
        description="Raw IR JSON export",
    )
    registry.register_output(
        "txt",
        TextRenderer,
        binary=False,
        description="Plain text",
    )

    # Binary backends (not IR-based)
    # These use lazy import wrappers so optional deps aren't required at import time.
    from pdf2any.backends.docx_backend import DOCXRenderer
    from pdf2any.backends.image_backend import ImageRendererJPG, ImageRendererPNG

    registry.register_output(
        "docx",
        DOCXRenderer,
        binary=True,
        description="DOCX via pdf2docx (isolated backend)",
        notes="Requires pdf2docx: pip install pdf2any[docx]",
    )
    registry.register_output(
        "png",
        ImageRendererPNG,
        binary=True,
        description="Page images (PNG)",
    )
    registry.register_output(
        "jpg",
        ImageRendererJPG,
        binary=True,
        description="Page images (JPG)",
    )

    return registry
