"""Tests for the ProseMirror JSON renderer."""

from __future__ import annotations

import json

from pdf2any.ir import (
    Blockquote,
    BulletList,
    CodeBlock,
    Emphasis,
    Heading,
    IRDocument,
    Image,
    LineBreak,
    Link,
    ListItem,
    OrderedList,
    PageBreak,
    Paragraph,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
)
from pdf2any.renderers.prosemirror_renderer import ProseMirrorRenderer


class TestProseMirrorRenderer:
    """Tests for ProseMirror JSON output."""

    def setup_method(self):
        self.renderer = ProseMirrorRenderer()

    def test_root_is_doc(self):
        """Root node must be {"type": "doc", "content": [...]}."""
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hi")])])
        result = self.renderer.render(doc)
        data = json.loads(result)
        assert data["type"] == "doc"
        assert isinstance(data["content"], list)

    def test_heading(self):
        doc = IRDocument(children=[Heading(level=2, content=[Text(text="Section")])])
        data = json.loads(self.renderer.render(doc))
        node = data["content"][0]
        assert node["type"] == "heading"
        assert node["attrs"]["level"] == 2
        assert node["content"][0]["text"] == "Section"

    def test_paragraph(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hello")])])
        data = json.loads(self.renderer.render(doc))
        node = data["content"][0]
        assert node["type"] == "paragraph"
        assert node["content"][0]["text"] == "Hello"

    def test_text_with_strong_mark(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="bold", marks=[Strong()])]),
        ])
        data = json.loads(self.renderer.render(doc))
        text_node = data["content"][0]["content"][0]
        assert text_node["type"] == "text"
        assert text_node["text"] == "bold"
        assert text_node["marks"][0]["type"] == "strong"

    def test_text_with_em_mark(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="italic", marks=[Emphasis()])]),
        ])
        data = json.loads(self.renderer.render(doc))
        marks = data["content"][0]["content"][0]["marks"]
        assert any(m["type"] == "em" for m in marks)

    def test_text_with_link_mark(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="click", marks=[Link(href="https://example.com")])]),
        ])
        data = json.loads(self.renderer.render(doc))
        marks = data["content"][0]["content"][0]["marks"]
        link_mark = [m for m in marks if m["type"] == "link"][0]
        assert link_mark["attrs"]["href"] == "https://example.com"

    def test_bullet_list(self):
        doc = IRDocument(children=[
            BulletList(items=[
                ListItem(content=[Paragraph(content=[Text(text="A")])]),
                ListItem(content=[Paragraph(content=[Text(text="B")])]),
            ]),
        ])
        data = json.loads(self.renderer.render(doc))
        node = data["content"][0]
        assert node["type"] == "bullet_list"
        assert len(node["content"]) == 2
        assert node["content"][0]["type"] == "list_item"
        # list_item contains paragraph
        assert node["content"][0]["content"][0]["type"] == "paragraph"

    def test_ordered_list_with_start(self):
        doc = IRDocument(children=[
            OrderedList(
                items=[ListItem(content=[Paragraph(content=[Text(text="A")])])],
                start=3,
            ),
        ])
        data = json.loads(self.renderer.render(doc))
        node = data["content"][0]
        assert node["type"] == "ordered_list"
        assert node["attrs"]["start"] == 3

    def test_blockquote(self):
        doc = IRDocument(children=[
            Blockquote(content=[Paragraph(content=[Text(text="Quote")])]),
        ])
        data = json.loads(self.renderer.render(doc))
        node = data["content"][0]
        assert node["type"] == "blockquote"
        assert node["content"][0]["type"] == "paragraph"

    def test_image(self):
        doc = IRDocument(children=[Image(src="img.png", alt="Alt text")])
        data = json.loads(self.renderer.render(doc))
        node = data["content"][0]
        assert node["type"] == "image"
        assert node["attrs"]["src"] == "img.png"
        assert node["attrs"]["alt"] == "Alt text"

    def test_code_block(self):
        doc = IRDocument(children=[CodeBlock(content="x=1", language="python")])
        data = json.loads(self.renderer.render(doc))
        node = data["content"][0]
        assert node["type"] == "code_block"

    def test_table_degrades_to_paragraphs(self):
        """Tables should degrade to paragraphs, not fail."""
        doc = IRDocument(children=[
            Table(rows=[
                TableRow(cells=[
                    TableCell(content=[Text(text="A")]),
                    TableCell(content=[Text(text="B")]),
                ]),
            ]),
        ])
        data = json.loads(self.renderer.render(doc))
        # First content node should be a paragraph (degraded table)
        node = data["content"][0]
        assert node["type"] == "paragraph"

    def test_page_break_degrades(self):
        """PageBreak should not cause errors (degrades to None/skipped)."""
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="Before")]),
            PageBreak(),
            Paragraph(content=[Text(text="After")]),
        ])
        data = json.loads(self.renderer.render(doc))
        # Should have 2 content nodes (page break skipped)
        assert len(data["content"]) == 2

    def test_empty_paragraph_gets_empty_text(self):
        """ProseMirror requires content arrays; empty paragraph gets empty text."""
        doc = IRDocument(children=[Paragraph(content=[])])
        data = json.loads(self.renderer.render(doc))
        node = data["content"][0]
        assert node["type"] == "paragraph"
        assert len(node["content"]) >= 1

    def test_pretty_output(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hi")])])
        result = self.renderer.render(doc, pretty=True)
        # Pretty output has newlines/indentation
        assert "\n" in result

    def test_compact_output(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hi")])])
        result = self.renderer.render(doc, pretty=False)
        # Compact output is single-line
        assert result.count("\n") == 0

    def test_valid_json(self):
        """Output must be valid JSON."""
        doc = IRDocument(children=[
            Heading(level=1, content=[Text(text="Title")]),
            Paragraph(content=[Text(text="Body")]),
        ])
        result = self.renderer.render(doc)
        # Must not raise
        json.loads(result)

    def test_full_document(self, sample_ir):
        """Test rendering the full sample IR."""
        result = self.renderer.render(sample_ir)
        data = json.loads(result)
        assert data["type"] == "doc"
        assert len(data["content"]) > 5  # Multiple nodes

    def test_list_item_must_contain_blocks(self):
        """list_item nodes must contain block content (paragraphs), not bare text."""
        doc = IRDocument(children=[
            BulletList(items=[
                ListItem(content=[Paragraph(content=[Text(text="Item")])]),
            ]),
        ])
        data = json.loads(self.renderer.render(doc))
        list_item = data["content"][0]["content"][0]
        assert list_item["type"] == "list_item"
        # Content should be a paragraph (block), not bare text
        assert list_item["content"][0]["type"] == "paragraph"

    def test_multiple_marks_on_text(self):
        """A text node can have multiple marks."""
        doc = IRDocument(children=[
            Paragraph(content=[
                Text(text="bold+link", marks=[Strong(), Link(href="https://x.com")]),
            ]),
        ])
        data = json.loads(self.renderer.render(doc))
        text_node = data["content"][0]["content"][0]
        assert len(text_node["marks"]) == 2
        mark_types = {m["type"] for m in text_node["marks"]}
        assert "strong" in mark_types
        assert "link" in mark_types
