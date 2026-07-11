"""Tests for the JSON and Text renderers."""

from __future__ import annotations

import json

from pdf2any.ir import (
    CodeBlock,
    Heading,
    IRDocument,
    Paragraph,
    Text,
)
from pdf2any.renderers.json_renderer import JSONRenderer
from pdf2any.renderers.text_renderer import TextRenderer


class TestJSONRenderer:
    """Tests for raw IR JSON output."""

    def setup_method(self):
        self.renderer = JSONRenderer()

    def test_json_output_is_valid(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hi")])])
        result = self.renderer.render(doc)
        data = json.loads(result)
        assert data["type"] == "document"
        assert "ir_version" in data

    def test_json_pretty(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hi")])])
        result = self.renderer.render(doc, pretty=True)
        assert "\n" in result

    def test_json_compact(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hi")])])
        result = self.renderer.render(doc, pretty=False)
        assert "\n" not in result

    def test_json_contains_metadata(self):
        from pdf2any.ir import PDFMetadata

        doc = IRDocument(
            metadata=PDFMetadata(title="Test", page_count=5),
            children=[],
        )
        data = json.loads(self.renderer.render(doc))
        assert data["metadata"]["title"] == "Test"

    def test_json_contains_children(self):
        doc = IRDocument(children=[
            Heading(level=1, content=[Text(text="Title")]),
            Paragraph(content=[Text(text="Body")]),
        ])
        data = json.loads(self.renderer.render(doc))
        assert len(data["children"]) == 2


class TestTextRenderer:
    """Tests for plain text output."""

    def setup_method(self):
        self.renderer = TextRenderer()

    def test_heading(self):
        doc = IRDocument(children=[Heading(level=1, content=[Text(text="Title")])])
        result = self.renderer.render(doc)
        assert "TITLE" in result  # Level 1-2 headings are uppercased

    def test_paragraph(self):
        doc = IRDocument(children=[Paragraph(content=[Text(text="Hello.")])])
        result = self.renderer.render(doc)
        assert "Hello." in result

    def test_code_block(self):
        doc = IRDocument(children=[CodeBlock(content="x = 1")])
        result = self.renderer.render(doc)
        assert "x = 1" in result

    def test_strips_marks(self):
        """Text renderer should strip all formatting marks."""
        from pdf2any.ir import Strong

        doc = IRDocument(children=[
            Paragraph(content=[Text(text="bold", marks=[Strong()])]),
        ])
        result = self.renderer.render(doc)
        # No markdown/HTML markup, just plain text
        assert "bold" in result
        assert "**" not in result
        assert "<strong>" not in result
