"""HTML renderer — converts IR to HTML.

By default produces an HTML fragment. With ``--standalone`` produces a
full HTML document with <html>, <head>, and <body> wrapper.
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


class HTMLRenderer(Renderer):
    """Render IR to HTML."""

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
        """Render the IR document to HTML."""
        body_parts: list[str] = []

        for child in doc.children:
            rendered = self._render_block(child)
            if rendered:
                body_parts.append(rendered)

        body = "\n".join(body_parts)

        if not standalone:
            return body

        # Full standalone HTML document
        title = self._escape(doc.metadata.title or "PDF Document")
        indent = "  " if pretty else ""
        newline = "\n" if pretty else ""

        lines = [
            f"<!DOCTYPE html>{newline}",
            f"<html lang=\"en\">{newline}",
            f"{indent}<head>{newline}",
            f"{indent}{indent}<meta charset=\"utf-8\">{newline}",
            f"{indent}{indent}<title>{title}</title>{newline}",
            f"{indent}</head>{newline}",
            f"{indent}<body>{newline}",
        ]

        if pretty:
            # Indent body lines
            body_lines = body.split("\n")
            body = "\n".join(f"{indent}{indent}{line}" if line else line for line in body_lines)

        lines.append(f"{body}{newline}")
        lines.append(f"{indent}</body>{newline}")
        lines.append("</html>")

        return "".join(lines)

    def _render_block(self, node: BlockNode) -> str:
        """Render a single block node to HTML."""
        if isinstance(node, Heading):
            text = self._render_inline_list(node.content)
            return f"<h{node.level}>{text}</h{node.level}>"

        if isinstance(node, Paragraph):
            text = self._render_inline_list(node.content)
            return f"<p>{text}</p>"

        if isinstance(node, BulletList):
            items = "".join(
                f"<li>{self._render_blocks(item.content)}</li>"
                for item in node.items
            )
            return f"<ul>{items}</ul>"

        if isinstance(node, OrderedList):
            start_attr = f' start="{node.start}"' if node.start != 1 else ""
            items = "".join(
                f"<li>{self._render_blocks(item.content)}</li>"
                for item in node.items
            )
            return f"<ol{start_attr}>{items}</ol>"

        if isinstance(node, Blockquote):
            inner = self._render_blocks(node.content)
            return f"<blockquote>{inner}</blockquote>"

        if isinstance(node, Table):
            return self._render_table(node)

        if isinstance(node, Image):
            alt = self._escape(node.alt or "image")
            return f'<img src="{self._escape(node.src)}" alt="{alt}">'

        if isinstance(node, CodeBlock):
            lang_attr = f' class="language-{node.language}"' if node.language else ""
            return f"<pre><code{lang_attr}>{self._escape(node.content)}</code></pre>"

        if isinstance(node, PageBreak):
            return "<hr>"

        if isinstance(node, LineBreak):
            return "<br>"

        return ""

    def _render_table(self, node: Table) -> str:
        """Render a table to HTML."""
        if not node.rows:
            return ""

        lines: list[str] = ["<table>"]

        for row in node.rows:
            cells_html: list[str] = []
            for cell in row.cells:
                content = self._render_inline_list(cell.content)
                tag = "th" if row.header else "td"
                attrs = ""
                if cell.colspan > 1:
                    attrs += f' colspan="{cell.colspan}"'
                if cell.rowspan > 1:
                    attrs += f' rowspan="{cell.rowspan}"'
                cells_html.append(f"<{tag}{attrs}>{content}</{tag}>")
            lines.append(f"<tr>{''.join(cells_html)}</tr>")

        lines.append("</table>")
        return "".join(lines)

    def _render_inline_list(self, nodes: list[InlineNode]) -> str:
        """Render a list of inline nodes to HTML."""
        return "".join(self._render_inline(n) for n in nodes)

    def _render_inline(self, node: InlineNode) -> str:
        """Render a single inline node to HTML."""
        if not isinstance(node, Text):
            return self._escape(str(getattr(node, "text", "")))

        text = self._escape(node.text)
        if not node.marks:
            return text

        # Apply marks (outermost first for HTML)
        for mark in node.marks:
            text = self._apply_mark(mark, text)
        return text

    def _apply_mark(self, mark: Mark, text: str) -> str:
        """Wrap text with HTML tags for a mark."""
        if isinstance(mark, Strong):
            return f"<strong>{text}</strong>"
        if isinstance(mark, Emphasis):
            return f"<em>{text}</em>"
        if isinstance(mark, Code):
            return f"<code>{text}</code>"
        if isinstance(mark, Link):
            href = self._escape(mark.href)
            return f'<a href="{href}">{text}</a>'
        return text

    def _render_blocks(self, nodes: list[BlockNode]) -> str:
        """Render a list of block nodes."""
        return "".join(self._render_block(n) for n in nodes)

    @staticmethod
    def _escape(text: str) -> str:
        """Escape HTML special characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
