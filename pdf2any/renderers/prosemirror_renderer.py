"""ProseMirror JSON renderer.

Outputs valid ProseMirror-style JSON with a root ``doc`` node:

    { "type": "doc", "content": [...] }

Supported node types:
    - heading (attrs.level)
    - paragraph
    - bullet_list / ordered_list (attrs.start) → list_item
    - blockquote
    - image (attrs.src, attrs.alt)
    - text (with marks: strong, em, code, link)
    - table > table_row > table_header / table_cell (prosemirror-tables schema)
    - horizontal_rule (for page breaks)

Schema alignment:
    - doc contains block nodes
    - paragraphs contain inline content (text nodes)
    - list nodes contain list_item nodes
    - list_item nodes contain block content (paragraphs)
    - tables use prosemirror-tables schema:
      table > table_row > (table_header | table_cell) > paragraph > text
    - page breaks render as horizontal_rule nodes
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

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
    from pdf2any.ir import BlockNode, InlineNode, IRDocument, ListItem, Mark


class ProseMirrorRenderer(Renderer):
    """Render IR to ProseMirror JSON.

    Produces a JSON object with ``"type": "doc"`` as root and a
    ``content`` array of block nodes.
    """

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
        """Render the IR document to ProseMirror JSON string."""
        content: list[dict[str, Any]] = []

        for child in doc.children:
            node = self._render_block(child)
            if node:
                if isinstance(node, list):
                    content.extend(node)
                else:
                    content.append(node)

        result: dict[str, Any] = {"type": "doc", "content": content}

        if pretty:
            return json.dumps(result, indent=2, ensure_ascii=False)
        return json.dumps(result, ensure_ascii=False)

    def _render_block(self, node: BlockNode) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Render a block node to a ProseMirror JSON node dict.

        Returns None for nodes that should be skipped (e.g. PageBreak
        degrades to nothing in ProseMirror, or a horizontal rule if
        we wanted to support it — but basic schema doesn't include it).
        """
        if isinstance(node, Heading):
            return {
                "type": "heading",
                "attrs": {"level": node.level},
                "content": self._render_inline_list(node.content),
            }

        if isinstance(node, Paragraph):
            content = self._render_inline_list(node.content)
            if not content:
                # ProseMirror requires content arrays to be non-empty
                # for paragraphs in most schemas; use empty text node
                content = [{"type": "text", "text": ""}]
            return {"type": "paragraph", "content": content}

        if isinstance(node, BulletList):
            items = [self._render_list_item(item) for item in node.items]
            return {"type": "bullet_list", "content": items}

        if isinstance(node, OrderedList):
            items = [self._render_list_item(item) for item in node.items]
            return {
                "type": "ordered_list",
                "attrs": {"start": node.start},
                "content": items,
            }

        if isinstance(node, Blockquote):
            content: list[dict[str, Any]] = []
            for child in node.content:
                rendered = self._render_block(child)
                if rendered and not isinstance(rendered, list):
                    content.append(rendered)
                elif isinstance(rendered, list):
                    content.extend(rendered)
            if not content:
                content = [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]
            return {"type": "blockquote", "content": content}

        if isinstance(node, Image):
            return {
                "type": "image",
                "attrs": {"src": node.src, "alt": node.alt or ""},
            }

        if isinstance(node, CodeBlock):
            # ProseMirror code_block contains text nodes
            return {
                "type": "code_block",
                "content": [{"type": "text", "text": node.content}],
            }

        if isinstance(node, Table):
            return self._render_table(node)

        if isinstance(node, PageBreak):
            # Render as horizontal_rule (standard ProseMirror basic schema node)
            return {"type": "horizontal_rule"}

        if isinstance(node, LineBreak):
            # hard_break node in ProseMirror
            return {"type": "hard_break"}

        # Unknown → degrade to paragraph
        text_content = str(getattr(node, "text", getattr(node, "content", "")))
        return {
            "type": "paragraph",
            "content": [{"type": "text", "text": text_content}],
        }

    def _render_list_item(self, item: ListItem) -> dict[str, Any]:
        """Render a list item to ProseMirror JSON.

        list_item nodes contain block content (typically paragraphs).
        """
        content: list[dict[str, Any]] = []
        for child in item.content:
            rendered = self._render_block(child)
            if rendered and not isinstance(rendered, list):
                content.append(rendered)
            elif isinstance(rendered, list):
                content.extend(rendered)

        if not content:
            content = [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}]

        return {"type": "list_item", "content": content}

    def _render_inline_list(self, nodes: list[InlineNode]) -> list[dict[str, Any]]:
        """Render inline nodes to ProseMirror text node dicts."""
        result: list[dict[str, Any]] = []
        for node in nodes:
            if isinstance(node, Text):
                if not node.text:
                    continue
                text_node: dict[str, Any] = {"type": "text", "text": node.text}
                marks = self._render_marks(node.marks)
                if marks:
                    text_node["marks"] = marks
                result.append(text_node)
            # Unknown inline nodes are skipped
        return result

    def _render_marks(self, marks: list[Mark]) -> list[dict[str, Any]]:
        """Render IR marks to ProseMirror mark dicts."""
        result: list[dict[str, Any]] = []
        for mark in marks:
            if isinstance(mark, Strong):
                result.append({"type": "strong"})
            elif isinstance(mark, Emphasis):
                result.append({"type": "em"})
            elif isinstance(mark, Code):
                result.append({"type": "code"})
            elif isinstance(mark, Link):
                result.append({"type": "link", "attrs": {"href": mark.href}})
        return result

    def _render_table(self, table: Table) -> dict[str, Any]:
        """Render a table using the prosemirror-tables schema.

        Structure:
            table
              └─ table_row
                   └─ table_header | table_cell
                        └─ paragraph
                             └─ text

        Header rows use ``table_header`` cells; body rows use ``table_cell``.
        Each cell wraps its inline content in a paragraph (required by
        the prosemirror-tables schema).
        """
        rows: list[dict[str, Any]] = []

        for ir_row in table.rows:
            cells: list[dict[str, Any]] = []
            for ir_cell in ir_row.cells:
                cell_type = "table_header" if ir_row.header else "table_cell"
                cell_content = self._render_inline_list(ir_cell.content)
                if not cell_content:
                    cell_content = [{"type": "text", "text": ""}]

                cell_node: dict[str, Any] = {
                    "type": cell_type,
                    "content": [
                        {"type": "paragraph", "content": cell_content}
                    ],
                }

                # Include colspan/rowspan if non-default
                attrs: dict[str, Any] = {}
                if ir_cell.colspan > 1:
                    attrs["colspan"] = ir_cell.colspan
                if ir_cell.rowspan > 1:
                    attrs["rowspan"] = ir_cell.rowspan
                if attrs:
                    cell_node["attrs"] = attrs

                cells.append(cell_node)

            rows.append({"type": "table_row", "content": cells})

        return {"type": "table", "content": rows}
