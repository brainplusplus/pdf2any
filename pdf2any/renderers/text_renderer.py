"""Text renderer — converts IR to plain text.

Strips all markup and produces readable plain text. Tables are rendered
as tab/space-aligned text. Images are represented as their alt text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pdf2any.ir import (
    Blockquote,
    BulletList,
    CodeBlock,
    Heading,
    Image,
    LineBreak,
    OrderedList,
    PageBreak,
    Paragraph,
    Table,
    Text,
)
from pdf2any.renderers.base import Renderer

if TYPE_CHECKING:
    from pdf2any.ir import BlockNode, InlineNode, IRDocument


class TextRenderer(Renderer):
    """Render IR to plain text."""

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
        """Render the IR document to plain text."""
        lines: list[str] = []

        for child in doc.children:
            rendered = self._render_block(child)
            if rendered:
                lines.append(rendered)
                lines.append("")  # Blank line between blocks

        return "\n".join(lines).strip() + "\n"

    def _render_block(self, node: BlockNode) -> str:
        """Render a single block node to plain text."""
        if isinstance(node, Heading):
            text = self._render_inline_list(node.content)
            # Headings: uppercase for level 1-2, plain for others
            if node.level <= 2:
                return text.upper()
            return text

        if isinstance(node, Paragraph):
            return self._render_inline_list(node.content)

        if isinstance(node, BulletList):
            lines: list[str] = []
            for item in node.items:
                item_text = self._render_blocks(item.content)
                lines.append(f"  • {item_text}")
            return "\n".join(lines)

        if isinstance(node, OrderedList):
            lines = []
            for i, item in enumerate(node.items):
                num = node.start + i
                item_text = self._render_blocks(item.content)
                lines.append(f"  {num}. {item_text}")
            return "\n".join(lines)

        if isinstance(node, Blockquote):
            inner = self._render_blocks(node.content)
            return "\n".join(f"  > {line}" for line in inner.split("\n"))

        if isinstance(node, Table):
            return self._render_table(node)

        if isinstance(node, Image):
            return f"[{node.alt or 'image'}]"

        if isinstance(node, CodeBlock):
            return node.content

        if isinstance(node, PageBreak):
            return "\f"  # Form feed character

        if isinstance(node, LineBreak):
            return ""

        return ""

    def _render_table(self, node: Table) -> str:
        """Render a table as plain text with tab separation."""
        if not node.rows:
            return ""

        lines: list[str] = []
        for row in node.rows:
            cells = [self._render_inline_list(c.content) for c in row.cells]
            lines.append("\t".join(cells))
        return "\n".join(lines)

    def _render_inline_list(self, nodes: list[InlineNode]) -> str:
        """Render inline nodes to plain text (strips marks)."""
        parts: list[str] = []
        for node in nodes:
            if isinstance(node, Text):
                parts.append(node.text)
            else:
                parts.append(str(getattr(node, "text", "")))
        return "".join(parts)

    def _render_blocks(self, nodes: list[BlockNode]) -> str:
        """Render a list of block nodes."""
        parts: list[str] = []
        for node in nodes:
            rendered = self._render_block(node)
            if rendered:
                parts.append(rendered)
        return "\n".join(parts)
