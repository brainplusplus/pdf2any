"""Shared test fixtures for pdf2any tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdf2any.ir import (
    Blockquote,
    BulletList,
    CodeBlock,
    Heading,
    Image,
    IRDocument,
    LineBreak,
    Link,
    OrderedList,
    PageBreak,
    Paragraph,
    PDFMetadata,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_ir() -> IRDocument:
    """A sample IRDocument with various node types for renderer tests."""
    doc = IRDocument(
        metadata=PDFMetadata(
            title="Sample Document",
            author="Test Author",
            page_count=3,
        ),
        children=[
            Heading(level=1, content=[Text(text="Document Title")]),
            Paragraph(content=[
                Text(text="A paragraph with "),
                Text(text="bold", marks=[Strong()]),
                Text(text=" and "),
                Text(text="a link", marks=[Link(href="https://example.com")]),
                Text(text="."),
            ]),
            Heading(level=2, content=[Text(text="Lists")]),
            BulletList(items=[
                _list_item("First item"),
                _list_item("Second item"),
                _list_item("Third item"),
            ]),
            OrderedList(
                items=[
                    _list_item("First"),
                    _list_item("Second"),
                ],
                start=1,
            ),
            Heading(level=2, content=[Text(text="A Table")]),
            Table(rows=[
                TableRow(
                    cells=[
                        TableCell(content=[Text(text="Name")]),
                        TableCell(content=[Text(text="Value")]),
                    ],
                    header=True,
                ),
                TableRow(cells=[
                    TableCell(content=[Text(text="Alpha")]),
                    TableCell(content=[Text(text="100")]),
                ]),
            ]),
            Heading(level=2, content=[Text(text="Quote")]),
            Blockquote(content=[
                Paragraph(content=[Text(text="This is a quote.")]),
            ]),
            CodeBlock(content="print('hello world')", language="python"),
            Image(src="image1.png", alt="A diagram"),
            Paragraph(content=[
                Text(text="Final paragraph."),
                LineBreak(),
                Text(text="After a line break."),
            ]),
            PageBreak(),
        ],
    )
    return doc


def _list_item(text: str):
    """Helper to create a ListItem containing a paragraph."""
    from pdf2any.ir import ListItem

    return ListItem(content=[Paragraph(content=[Text(text=text)])])


@pytest.fixture
def minimal_ir() -> IRDocument:
    """A minimal IRDocument with just a heading and paragraph."""
    return IRDocument(
        metadata=PDFMetadata(title="Minimal", page_count=1),
        children=[
            Heading(level=1, content=[Text(text="Title")]),
            Paragraph(content=[Text(text="Hello, world.")]),
        ],
    )
