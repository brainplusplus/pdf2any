"""Tests for the Markdown renderer."""

from __future__ import annotations

from pdf2any.ir import (
    BulletList,
    CodeBlock,
    Heading,
    IRDocument,
    LineBreak,
    Link,
    OrderedList,
    PageBreak,
    Paragraph,
    Table,
    TableCell,
    TableRow,
    Text,
)
from pdf2any.ir import ListItem
from pdf2any.ir import Strong, Emphasis, Code
from pdf2any.renderers.markdown_renderer import MarkdownRenderer


class TestMarkdownRenderer:
    """Tests for Markdown output."""

    def setup_method(self):
        self.renderer = MarkdownRenderer()

    def test_heading(self):
        doc = IRDocument(children=[Heading(level=2, content=[Text(text="Section")])])
        result = self.renderer.render(doc)
        assert "## Section" in result

    def test_paragraph(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hello world.")])])
        result = self.renderer.render(doc)
        assert "Hello world." in result

    def test_bold_text(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="bold", marks=[Strong()])]),
        ])
        result = self.renderer.render(doc)
        assert "**bold**" in result

    def test_italic_text(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="italic", marks=[Emphasis()])]),
        ])
        result = self.renderer.render(doc)
        assert "*italic*" in result

    def test_code_mark(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="code", marks=[Code()])]),
        ])
        result = self.renderer.render(doc)
        assert "`code`" in result

    def test_link(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="link", marks=[Link(href="https://example.com")])]),
        ])
        result = self.renderer.render(doc)
        assert "[link](https://example.com)" in result

    def test_bullet_list(self):
        doc = IRDocument(children=[
            BulletList(items=[
                ListItem(content=[Paragraph(content=[Text(text="Item 1")])]),
                ListItem(content=[Paragraph(content=[Text(text="Item 2")])]),
            ]),
        ])
        result = self.renderer.render(doc)
        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_ordered_list(self):
        doc = IRDocument(children=[
            OrderedList(
                items=[
                    ListItem(content=[Paragraph(content=[Text(text="First")])]),
                    ListItem(content=[Paragraph(content=[Text(text="Second")])]),
                ],
                start=1,
            ),
        ])
        result = self.renderer.render(doc)
        assert "1. First" in result
        assert "2. Second" in result

    def test_ordered_list_custom_start(self):
        doc = IRDocument(children=[
            OrderedList(
                items=[
                    ListItem(content=[Paragraph(content=[Text(text="A")])]),
                ],
                start=5,
            ),
        ])
        result = self.renderer.render(doc)
        assert "5. A" in result

    def test_table(self):
        doc = IRDocument(children=[
            Table(rows=[
                TableRow(cells=[
                    TableCell(content=[Text(text="Name")]),
                    TableCell(content=[Text(text="Value")]),
                ], header=True),
                TableRow(cells=[
                    TableCell(content=[Text(text="x")]),
                    TableCell(content=[Text(text="42")]),
                ]),
            ]),
        ])
        result = self.renderer.render(doc)
        assert "| Name | Value |" in result
        assert "| --- | --- |" in result
        assert "| x | 42 |" in result

    def test_code_block(self):
        doc = IRDocument(children=[CodeBlock(content="print('hi')", language="python")])
        result = self.renderer.render(doc)
        assert "```python" in result
        assert "print('hi')" in result

    def test_page_break(self):
        doc = IRDocument(children=[PageBreak()])
        result = self.renderer.render(doc)
        assert "---" in result

    def test_standalone_with_title(self):
        doc = IRDocument(
            metadata=__import__("pdf2any.ir", fromlist=["PDFMetadata"]).PDFMetadata(
                title="My Doc", page_count=1
            ),
            children=[Paragraph(content=[Text(text="Content")])],
        )
        result = self.renderer.render(doc, standalone=True)
        assert "# My Doc" in result

    def test_full_document(self, sample_ir):
        """Test rendering a full IR document with multiple node types."""
        result = self.renderer.render(sample_ir)
        assert "# Document Title" in result
        assert "**bold**" in result
        assert "[a link](https://example.com)" in result
        assert "- First item" in result
        assert "1. First" in result
        assert "```python" in result
        assert "![A diagram](image1.png)" in result
