"""Tests for the HTML renderer."""

from __future__ import annotations

from pdf2any.ir import (
    CodeBlock,
    Heading,
    IRDocument,
    LineBreak,
    Link,
    Paragraph,
    PDFMetadata,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
)
from pdf2any.renderers.html_renderer import HTMLRenderer


class TestHTMLRenderer:
    """Tests for HTML output."""

    def setup_method(self):
        self.renderer = HTMLRenderer()

    def test_heading(self):
        doc = IRDocument(children=[Heading(level=3, content=[Text(text="Section")])])
        result = self.renderer.render(doc)
        assert "<h3>Section</h3>" in result

    def test_paragraph(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hello.")])])
        result = self.renderer.render(doc)
        assert "<p>Hello.</p>" in result

    def test_bold(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="bold", marks=[Strong()])]),
        ])
        result = self.renderer.render(doc)
        assert "<strong>bold</strong>" in result

    def test_link(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="click", marks=[Link(href="https://example.com")])]),
        ])
        result = self.renderer.render(doc)
        assert '<a href="https://example.com">click</a>' in result

    def test_code_block(self):
        doc = IRDocument(children=[CodeBlock(content="x=1", language="python")])
        result = self.renderer.render(doc)
        assert "<pre><code" in result
        assert "x=1" in result

    def test_html_escaping(self):
        doc = IRDocument(children=[
            Paragraph(content=[Text(text="<script>alert('xss')</script>")]),
        ])
        result = self.renderer.render(doc)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_table(self):
        doc = IRDocument(children=[
            Table(rows=[
                TableRow(cells=[
                    TableCell(content=[Text(text="A")]),
                    TableCell(content=[Text(text="B")]),
                ], header=True),
            ]),
        ])
        result = self.renderer.render(doc)
        assert "<table>" in result
        assert "<th>A</th>" in result
        assert "<th>B</th>" in result

    def test_fragment_default(self):
        """Without --standalone, output is an HTML fragment (no <html>)."""
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hi")])])
        result = self.renderer.render(doc)
        assert "<html" not in result
        assert "<p>Hi</p>" in result

    def test_stalone_document(self):
        """With --standalone, output is a full HTML document."""
        doc = IRDocument(
            metadata=PDFMetadata(title="My Title", page_count=1),
            children=[Paragraph(content=[Text(text="Body")])],
        )
        result = self.renderer.render(doc, standalone=True)
        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "<title>My Title</title>" in result
        assert "<body>" in result
        assert "<p>Body</p>" in result

    def test_standalone_pretty(self):
        """Pretty-printed standalone HTML is indented."""
        doc = IRDocument(
            metadata=PDFMetadata(title="Test", page_count=1),
            children=[Paragraph(content=[Text(text="Hi")])],
        )
        result = self.renderer.render(doc, standalone=True, pretty=True)
        assert "  <head>" in result

    def test_full_document(self, sample_ir):
        """Test rendering the full sample IR."""
        result = self.renderer.render(sample_ir)
        assert "<h1>Document Title</h1>" in result
        assert "<strong>bold</strong>" in result
        assert "<ul>" in result
        assert "<ol>" in result
        assert "<table>" in result
        assert "<blockquote>" in result
        assert "<pre><code" in result
        assert "<img" in result
