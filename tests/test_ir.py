"""Tests for the IR (Intermediate Representation) module."""

from __future__ import annotations

import json

import pytest

from pdf2any.ir import (
    IR_VERSION,
    BoundingBox,
    BulletList,
    Code,
    CodeBlock,
    Emphasis,
    Heading,
    IRDocument,
    Image,
    LineBreak,
    Link,
    OrderedList,
    Page,
    PageBreak,
    Paragraph,
    PDFMetadata,
    SourceLocation,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
)


class TestValueObjects:
    """Tests for frozen value objects."""

    def test_boundingBox_creation(self):
        bbox = BoundingBox(x0=10, y0=20, x1=100, y1=80)
        assert bbox.width == 90
        assert bbox.height == 60

    def test_boundingBox_is_frozen(self):
        bbox = BoundingBox(x0=0, y0=0, x1=10, y1=10)
        with pytest.raises(Exception):
            bbox.x0 = 5  # type: ignore[misc]

    def test_sourceLocation(self):
        src = SourceLocation(page=3, bbox=BoundingBox(x0=0, y0=0, x1=10, y1=10))
        assert src.page == 3
        assert src.bbox is not None

    def test_sourceLocation_no_bbox(self):
        src = SourceLocation(page=1)
        assert src.bbox is None


class TestText:
    """Tests for Text inline node."""

    def test_plain_text(self):
        t = Text(text="hello")
        assert t.text == "hello"
        assert t.marks == []

    def test_text_with_marks(self):
        t = Text(text="bold", marks=[Strong(), Emphasis()])
        assert len(t.marks) == 2

    def test_text_type_validation(self):
        with pytest.raises(TypeError):
            Text(text=123)  # type: ignore[arg-type]

    def test_text_to_dict_plain(self):
        t = Text(text="hello")
        d = t.to_dict()
        assert d == {"type": "text", "text": "hello"}

    def test_text_to_dict_with_marks(self):
        t = Text(text="link", marks=[Link(href="https://example.com")])
        d = t.to_dict()
        assert d["marks"][0]["type"] == "link"
        assert d["marks"][0]["attrs"]["href"] == "https://example.com"


class TestHeading:
    """Tests for Heading block node."""

    def test_heading_creation(self):
        h = Heading(level=2, content=[Text(text="Section")])
        assert h.level == 2
        assert len(h.content) == 1

    def test_heading_level_validation(self):
        with pytest.raises(ValueError):
            Heading(level=0)

    def test_heading_level_too_high(self):
        with pytest.raises(ValueError):
            Heading(level=7)

    def test_heading_to_dict(self):
        h = Heading(level=1, content=[Text(text="Title")])
        d = h.to_dict()
        assert d["type"] == "heading"
        assert d["level"] == 1
        assert d["content"][0]["text"] == "Title"


class TestParagraph:
    """Tests for Paragraph block node."""

    def test_empty_paragraph(self):
        p = Paragraph()
        assert p.content == []

    def test_paragraph_with_content(self):
        p = Paragraph(content=[Text(text="Hello")])
        assert len(p.content) == 1

    def test_paragraph_to_dict(self):
        p = Paragraph(content=[Text(text="Hello")])
        d = p.to_dict()
        assert d["type"] == "paragraph"


class TestLists:
    """Tests for list nodes."""

    def test_bullet_list(self):
        from pdf2any.ir import ListItem

        bl = BulletList(items=[
            ListItem(content=[Paragraph(content=[Text(text="A")])]),
            ListItem(content=[Paragraph(content=[Text(text="B")])]),
        ])
        d = bl.to_dict()
        assert d["type"] == "bullet_list"
        assert len(d["content"]) == 2

    def test_ordered_list_with_start(self):
        from pdf2any.ir import ListItem

        ol = OrderedList(
            items=[ListItem(content=[Paragraph(content=[Text(text="A")])])],
            start=5,
        )
        d = ol.to_dict()
        assert d["type"] == "ordered_list"
        assert d["attrs"]["start"] == 5


class TestTable:
    """Tests for Table nodes."""

    def test_table_creation(self):
        t = Table(rows=[
            TableRow(cells=[
                TableCell(content=[Text(text="A")]),
                TableCell(content=[Text(text="B")]),
            ], header=True),
        ])
        d = t.to_dict()
        assert d["type"] == "table"
        assert d["rows"][0]["header"] is True

    def test_table_cell_colspan(self):
        cell = TableCell(content=[Text(text="span")], colspan=2)
        d = cell.to_dict()
        assert d["colspan"] == 2


class TestIRDocument:
    """Tests for the root IRDocument."""

    def test_empty_document(self):
        doc = IRDocument()
        assert doc.metadata.page_count == 0
        assert doc.children == []

    def test_document_to_dict_has_ir_version(self):
        doc = IRDocument()
        d = doc.to_dict()
        assert d["ir_version"] == IR_VERSION
        assert d["type"] == "document"

    def test_document_to_dict_has_metadata(self):
        doc = IRDocument(
            metadata=PDFMetadata(title="Test", author="Me", page_count=5),
        )
        d = doc.to_dict()
        assert d["metadata"]["title"] == "Test"
        assert d["metadata"]["author"] == "Me"

    def test_document_round_trip(self):
        """Test to_dict → from_dict round-trip preserves structure."""
        doc = IRDocument(
            metadata=PDFMetadata(title="Round Trip", page_count=2),
            children=[
                Heading(level=1, content=[Text(text="Title")]),
                Paragraph(content=[Text(text="Body text")]),
                BulletList(items=[]),
            ],
        )
        d = doc.to_dict()
        restored = IRDocument.from_dict(d)

        assert restored.metadata.title == "Round Trip"
        assert len(restored.children) == 3
        assert isinstance(restored.children[0], Heading)
        assert restored.children[0].level == 1
        assert isinstance(restored.children[1], Paragraph)
        assert isinstance(restored.children[2], BulletList)

    def test_document_round_trip_with_marks(self):
        """Test round-trip preserves text marks."""
        doc = IRDocument(
            children=[
                Paragraph(content=[
                    Text(text="bold", marks=[Strong()]),
                    Text(text="italic", marks=[Emphasis()]),
                    Text(text="code", marks=[Code()]),
                    Text(text="link", marks=[Link(href="https://example.com")]),
                ]),
            ],
        )
        d = doc.to_dict()
        restored = IRDocument.from_dict(d)

        para = restored.children[0]
        assert isinstance(para, Paragraph)
        assert len(para.content[0].marks) == 1
        assert isinstance(para.content[0].marks[0], Strong)
        assert isinstance(para.content[1].marks[0], Emphasis)
        assert isinstance(para.content[2].marks[0], Code)
        assert isinstance(para.content[3].marks[0], Link)
        assert para.content[3].marks[0].href == "https://example.com"

    def test_document_json_serializable(self):
        """The to_dict output must be JSON-serializable."""
        doc = IRDocument(
            children=[
                Heading(level=2, content=[Text(text="Section")]),
                Paragraph(content=[Text(text="Content")]),
            ],
        )
        json_str = json.dumps(doc.to_dict())
        assert '"type": "heading"' in json_str or '"type":"heading"' in json_str


class TestPageBreak:
    def test_page_break_to_dict(self):
        pb = PageBreak()
        assert pb.to_dict() == {"type": "page_break"}


class TestLineBreak:
    def test_line_break_to_dict(self):
        lb = LineBreak()
        assert lb.to_dict() == {"type": "line_break"}


class TestCodeBlock:
    def test_code_block_to_dict(self):
        cb = CodeBlock(content="print(1)", language="python")
        d = cb.to_dict()
        assert d["type"] == "code_block"
        assert d["content"] == "print(1)"
        assert d["language"] == "python"


class TestImage:
    def test_image_to_dict(self):
        img = Image(src="test.png", alt="Test")
        d = img.to_dict()
        assert d["type"] == "image"
        assert d["src"] == "test.png"
        assert d["alt"] == "Test"
