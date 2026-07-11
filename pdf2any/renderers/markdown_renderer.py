"""Markdown renderer — converts IR to semantic Markdown.

Produces best-effort Markdown with headings, paragraphs, lists, tables,
image references, code blocks, and inline marks (bold, italic, code, links).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pdf2any.ir import (
    Blockquote,
    BulletList,
    Code,
    CodeBlock,
    Emphasis,
    Heading,
    Image,
    LineBreak,
    Link,
    OrderedList,
    PageBreak,
    Paragraph,
    Strong,
    Table,
    Text,
)
from pdf2any.renderers.base import Renderer

if TYPE_CHECKING:
    from pdf2any.ir import BlockNode, InlineNode, IRDocument, Mark


class MarkdownRenderer(Renderer):
    """Render IR to semantic Markdown."""

    @property
    def is_binary(self) -> bool:
        return False

    def render(
        self,
        doc: IRDocument,
        *,
        standalone: bool = False,
        pretty: bool = False,
    ) -> str:
        """Render the IR document to Markdown text."""
        lines: list[str] = []

        # Optional metadata header (only in standalone mode)
        if standalone and doc.metadata.title:
            lines.append(f"# {doc.metadata.title}")
            lines.append("")

        # Render document children
        for child in doc.children:
            rendered = self._render_block(child)
            if rendered:
                lines.append(rendered)
                lines.append("")  # Blank line between blocks

        return "\n".join(lines).strip() + "\n"

    def _render_block(self, node: BlockNode) -> str:
        """Render a single block node to Markdown."""
        if isinstance(node, Heading):
            prefix = "#" * node.level
            text = self._render_inline_list(node.content)
            return f"{prefix} {text}"

        if isinstance(node, Paragraph):
            return self._render_inline_list(node.content)

        if isinstance(node, BulletList):
            return self._render_bullet_list(node)

        if isinstance(node, OrderedList):
            return self._render_ordered_list(node)

        if isinstance(node, Blockquote):
            inner = self._render_blocks(node.content)
            # Prefix each line with >
            prefixed = "\n".join(f"> {line}" if line else ">" for line in inner.split("\n"))
            return prefixed

        if isinstance(node, Table):
            return self._render_table(node)

        if isinstance(node, Image):
            alt = node.alt or "image"
            return f"![{alt}]({node.src})"

        if isinstance(node, CodeBlock):
            lang = node.language or ""
            return f"```{lang}\n{node.content}\n```"

        if isinstance(node, PageBreak):
            return "\n---\n"

        if isinstance(node, LineBreak):
            return "  \n"

        # Unknown block → paragraph fallback
        return str(node)

    def _render_bullet_list(self, node: BulletList) -> str:
        lines: list[str] = []
        for item in node.items:
            item_text = self._render_blocks(item.content)
            # First line gets bullet, subsequent lines indented
            item_lines = item_text.split("\n")
            lines.append(f"- {item_lines[0]}")
            for line in item_lines[1:]:
                if line.strip():
                    lines.append(f"  {line}")
        return "\n".join(lines)

    def _render_ordered_list(self, node: OrderedList) -> str:
        lines: list[str] = []
        for i, item in enumerate(node.items):
            num = node.start + i
            item_text = self._render_blocks(item.content)
            item_lines = item_text.split("\n")
            lines.append(f"{num}. {item_lines[0]}")
            for line in item_lines[1:]:
                if line.strip():
                    lines.append(f"   {line}")
        return "\n".join(lines)

    def _render_table(self, node: Table) -> str:
        """Render a table as a Markdown pipe table."""
        if not node.rows:
            return ""

        # Collect all rows as text
        rows_text: list[list[str]] = []
        for row in node.rows:
            cells = [self._render_inline_list(c.content) for c in row.cells]
            rows_text.append(cells)

        if not rows_text:
            return ""

        # Determine column count
        col_count = max(len(r) for r in rows_text)

        # Pad rows to uniform width
        for row in rows_text:
            while len(row) < col_count:
                row.append("")

        # First row is header
        header = rows_text[0]
        separator = ["---"] * col_count
        body = rows_text[1:] if len(rows_text) > 1 else []

        lines: list[str] = []
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(separator) + " |")
        for row in body:
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    def _render_inline_list(self, nodes: list[InlineNode]) -> str:
        """Render a list of inline nodes to Markdown text."""
        return "".join(self._render_inline(n) for n in nodes)

    def _render_inline(self, node: InlineNode) -> str:
        """Render a single inline node."""
        if not isinstance(node, Text):
            return str(getattr(node, "text", ""))

        text = node.text
        if not node.marks:
            return text

        # Apply marks (innermost first)
        result = text
        for mark in reversed(node.marks):
            result = self._apply_mark(mark, result)
        return result

    def _apply_mark(self, mark: Mark, text: str) -> str:
        """Wrap text with Markdown markup for a mark."""
        if isinstance(mark, Strong):
            return f"**{text}**"
        if isinstance(mark, Emphasis):
            return f"*{text}*"
        if isinstance(mark, Code):
            return f"`{text}`"
        if isinstance(mark, Link):
            return f"[{text}]({mark.href})"
        return text

    def _render_blocks(self, nodes: list[BlockNode]) -> str:
        """Render a list of block nodes."""
        parts: list[str] = []
        for node in nodes:
            rendered = self._render_block(node)
            if rendered:
                parts.append(rendered)
        return "\n\n".join(parts)
