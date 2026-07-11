"""Intermediate Representation (IR) for pdf2any.

All text/structured outputs render from this IR. The IR captures document
structure recovered from PDF via heuristic semantic normalization.

Design:
    - All nodes are ``@dataclass(slots=True)`` for low memory + fast attribute access.
    - Value objects (BoundingBox, SourceLocation, FontInfo) are frozen.
    - ``IRDocument.to_dict()`` / ``from_dict()`` provide JSON-serializable
      round-tripping. The serialized form always includes ``ir_version``.
    - ``__post_init__`` invariant checks enforce critical structural rules.

Node types:
    Block nodes:  Heading, Paragraph, BulletList, OrderedList, ListItem,
                  Blockquote, Table, TableRow, TableCell, Image, CodeBlock,
                  PageBreak, LineBreak
    Inline nodes: Text (carries marks: Emphasis, Strong, Code, Link)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Union

# ---------------------------------------------------------------------------
# IR version — bump when the serialized contract changes.
# ---------------------------------------------------------------------------

IR_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Value objects (frozen, hashable)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class BoundingBox:
    """A rectangular region on a PDF page, in PDF user-space coordinates."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass(slots=True, frozen=True)
class SourceLocation:
    """Where in the source PDF a node originated."""

    page: int  # 1-indexed
    bbox: BoundingBox | None = None


@dataclass(slots=True, frozen=True)
class FontInfo:
    """Font hints used for heading detection heuristics."""

    size: float
    name: str | None = None
    bold: bool = False
    italic: bool = False


# ---------------------------------------------------------------------------
# Mark nodes (inline modifiers on Text)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Emphasis:
    """Italic emphasis mark."""


@dataclass(slots=True)
class Strong:
    """Bold/strong mark."""


@dataclass(slots=True)
class Code:
    """Inline code mark."""


@dataclass(slots=True)
class Link:
    """Hyperlink mark."""

    href: str


Mark = Emphasis | Strong | Code | Link

# ---------------------------------------------------------------------------
# Inline nodes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Text:
    """A run of text with optional marks (emphasis, strong, code, link)."""

    text: str
    marks: list[Mark] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError(f"Text.text must be str, got {type(self.text).__name__}")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": "text", "text": self.text}
        if self.marks:
            d["marks"] = [_mark_to_dict(m) for m in self.marks]
        return d


InlineNode = Text  # extensible: future inline nodes can join this union

# ---------------------------------------------------------------------------
# Block nodes
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Heading:
    """A section heading.

    Attributes:
        level: 1–6, mapping to Markdown ``#`` depth or HTML ``<h1>``–``<h6>``.
        content: Inline text content of the heading.
    """

    level: int
    content: list[InlineNode] = field(default_factory=list)
    source: SourceLocation | None = None

    def __post_init__(self) -> None:
        if not (1 <= self.level <= 6):
            raise ValueError(f"Heading.level must be 1–6, got {self.level}")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": "heading",
            "level": self.level,
            "content": [n.to_dict() for n in self.content],
        }
        if self.source:
            d["source"] = _source_to_dict(self.source)
        return d


@dataclass(slots=True)
class Paragraph:
    """A paragraph of inline text content."""

    content: list[InlineNode] = field(default_factory=list)
    source: SourceLocation | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": "paragraph",
            "content": [n.to_dict() for n in self.content],
        }
        if self.source:
            d["source"] = _source_to_dict(self.source)
        return d


@dataclass(slots=True)
class ListItem:
    """An item in a bullet or ordered list. Content is block-level."""

    content: list[BlockNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"type": "list_item", "content": [n.to_dict() for n in self.content]}


@dataclass(slots=True)
class BulletList:
    """An unordered (bullet) list."""

    items: list[ListItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"type": "bullet_list", "content": [i.to_dict() for i in self.items]}


@dataclass(slots=True)
class OrderedList:
    """An ordered (numbered) list."""

    items: list[ListItem] = field(default_factory=list)
    start: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "ordered_list",
            "attrs": {"start": self.start},
            "content": [i.to_dict() for i in self.items],
        }


@dataclass(slots=True)
class Blockquote:
    """A block quotation."""

    content: list[BlockNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"type": "blockquote", "content": [n.to_dict() for n in self.content]}


@dataclass(slots=True)
class TableCell:
    """A single cell in a table row."""

    content: list[InlineNode] = field(default_factory=list)
    colspan: int = 1
    rowspan: int = 1

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": "table_cell",
            "content": [n.to_dict() for n in self.content],
            "colspan": self.colspan,
            "rowspan": self.rowspan,
        }
        return d


@dataclass(slots=True)
class TableRow:
    """A row of cells in a table."""

    cells: list[TableCell] = field(default_factory=list)
    header: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "table_row",
            "header": self.header,
            "cells": [c.to_dict() for c in self.cells],
        }


@dataclass(slots=True)
class Table:
    """A table with rows of cells."""

    rows: list[TableRow] = field(default_factory=list)
    source: SourceLocation | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": "table",
            "rows": [r.to_dict() for r in self.rows],
        }
        if self.source:
            d["source"] = _source_to_dict(self.source)
        return d


@dataclass(slots=True)
class Image:
    """An image reference extracted from the PDF."""

    src: str
    alt: str = ""
    bbox: BoundingBox | None = None
    source: SourceLocation | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": "image", "src": self.src, "alt": self.alt}
        if self.bbox:
            d["bbox"] = asdict(self.bbox)
        if self.source:
            d["source"] = _source_to_dict(self.source)
        return d


@dataclass(slots=True)
class CodeBlock:
    """A preformatted code block."""

    content: str = ""
    language: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": "code_block", "content": self.content}
        if self.language:
            d["language"] = self.language
        return d


@dataclass(slots=True)
class PageBreak:
    """An explicit page break marker."""

    def to_dict(self) -> dict[str, Any]:
        return {"type": "page_break"}


@dataclass(slots=True)
class LineBreak:
    """A hard line break within a paragraph."""

    def to_dict(self) -> dict[str, Any]:
        return {"type": "line_break"}


# BlockNode union — all block-level node types
BlockNode = Union[  # noqa: UP007
    "Heading",
    "Paragraph",
    "BulletList",
    "OrderedList",
    "ListItem",
    "Blockquote",
    "Table",
    "TableRow",
    "TableCell",
    "Image",
    "CodeBlock",
    "PageBreak",
    "LineBreak",
]

# ---------------------------------------------------------------------------
# Page and Document
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Page:
    """A single PDF page and its recovered block-level content."""

    page_number: int  # 1-indexed
    children: list[BlockNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "page",
            "page_number": self.page_number,
            "children": [_block_to_dict(child) for child in self.children],
        }


@dataclass(slots=True)
class PDFMetadata:
    """Metadata recovered from the PDF (title, author, etc.)."""

    title: str | None = None
    author: str | None = None
    subject: str | None = None
    creator: str | None = None
    producer: str | None = None
    creation_date: str | None = None
    mod_date: str | None = None
    page_count: int = 0
    encrypted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None and v != 0 or k == "page_count"}


@dataclass(slots=True)
class IRDocument:
    """Root IR node — the full document.

    This is what all renderers consume. Contains metadata, page-level
    structure, and a flat list of block children (the document body).
    """

    metadata: PDFMetadata = field(default_factory=PDFMetadata)
    pages: list[Page] = field(default_factory=list)
    children: list[BlockNode] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full IR to a JSON-compatible dict."""
        return {
            "ir_version": IR_VERSION,
            "type": "document",
            "metadata": self.metadata.to_dict(),
            "pages": [p.to_dict() for p in self.pages],
            "children": [_block_to_dict(child) for child in self.children],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> IRDocument:
        """Reconstruct an IRDocument from a serialized dict.

        This is intentionally tolerant — unknown keys are ignored so older
        IR versions can be loaded by newer code.
        """
        meta_d = d.get("metadata", {})
        metadata = PDFMetadata(
            title=meta_d.get("title"),
            author=meta_d.get("author"),
            subject=meta_d.get("subject"),
            creator=meta_d.get("creator"),
            producer=meta_d.get("producer"),
            creation_date=meta_d.get("creation_date"),
            mod_date=meta_d.get("mod_date"),
            page_count=meta_d.get("page_count", 0),
            encrypted=meta_d.get("encrypted", False),
        )
        children = [_block_from_dict(c) for c in d.get("children", [])]
        return cls(metadata=metadata, children=children)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

_MARK_TYPE_MAP: dict[str, type] = {
    "emphasis": Emphasis,
    "em": Emphasis,
    "strong": Strong,
    "code": Code,
    "link": Link,
}


def _mark_to_dict(mark: Mark) -> dict[str, Any]:
    """Serialize a mark to dict."""
    if isinstance(mark, Link):
        return {"type": "link", "attrs": {"href": mark.href}}
    # Emphasis, Strong, Code — just a type tag
    if isinstance(mark, Emphasis):
        return {"type": "em"}
    if isinstance(mark, Strong):
        return {"type": "strong"}
    if isinstance(mark, Code):
        return {"type": "code"}
    raise TypeError(f"Unknown mark type: {type(mark).__name__}")


def _mark_from_dict(d: dict[str, Any]) -> Mark:
    """Deserialize a mark from dict."""
    mtype = d.get("type", "")
    if mtype in ("emphasis", "em"):
        return Emphasis()
    if mtype == "strong":
        return Strong()
    if mtype == "code":
        return Code()
    if mtype == "link":
        return Link(href=d.get("attrs", {}).get("href", ""))
    raise TypeError(f"Unknown mark type: {mtype}")


def _source_to_dict(src: SourceLocation) -> dict[str, Any]:
    d: dict[str, Any] = {"page": src.page}
    if src.bbox:
        d["bbox"] = asdict(src.bbox)
    return d


def _text_from_dict(d: dict[str, Any]) -> Text:
    marks = [_mark_from_dict(m) for m in d.get("marks", [])]
    return Text(text=d.get("text", ""), marks=marks)


def _inline_from_dict(d: dict[str, Any]) -> InlineNode:
    node_type = d.get("type", "text")
    if node_type == "text":
        return _text_from_dict(d)
    # Unknown inline → wrap text
    return Text(text=d.get("text", ""))


def _block_to_dict(node: BlockNode) -> dict[str, Any]:
    """Serialize any block node to dict via its to_dict() method."""
    return node.to_dict()


def _block_from_dict(d: dict[str, Any]) -> BlockNode:
    """Deserialize a block node from dict."""
    node_type = d.get("type", "")

    if node_type == "heading":
        return Heading(
            level=d.get("level", 1),
            content=[_inline_from_dict(c) for c in d.get("content", [])],
        )
    if node_type == "paragraph":
        return Paragraph(content=[_inline_from_dict(c) for c in d.get("content", [])])
    if node_type == "bullet_list":
        return BulletList(
            items=[
                ListItem(content=[_block_from_dict(b) for b in i.get("content", [])])
                for i in d.get("content", [])
            ]
        )
    if node_type == "ordered_list":
        start = d.get("attrs", {}).get("start", 1)
        return OrderedList(
            items=[
                ListItem(content=[_block_from_dict(b) for b in i.get("content", [])])
                for i in d.get("content", [])
            ],
            start=start,
        )
    if node_type == "list_item":
        return ListItem(content=[_block_from_dict(b) for b in d.get("content", [])])
    if node_type == "blockquote":
        return Blockquote(content=[_block_from_dict(b) for b in d.get("content", [])])
    if node_type == "table":
        rows = []
        for r in d.get("rows", []):
            cells = [
                TableCell(
                    content=[_inline_from_dict(c) for c in cell.get("content", [])],
                    colspan=cell.get("colspan", 1),
                    rowspan=cell.get("rowspan", 1),
                )
                for cell in r.get("cells", [])
            ]
            rows.append(TableRow(cells=cells, header=r.get("header", False)))
        return Table(rows=rows)
    if node_type == "table_row":
        cells = [
            TableCell(
                content=[_inline_from_dict(c) for c in cell.get("content", [])],
                colspan=cell.get("colspan", 1),
                rowspan=cell.get("rowspan", 1),
            )
            for cell in d.get("cells", [])
        ]
        return TableRow(cells=cells, header=d.get("header", False))
    if node_type == "table_cell":
        return TableCell(
            content=[_inline_from_dict(c) for c in d.get("content", [])],
            colspan=d.get("colspan", 1),
            rowspan=d.get("rowspan", 1),
        )
    if node_type == "image":
        return Image(src=d.get("src", ""), alt=d.get("alt", ""))
    if node_type == "code_block":
        return CodeBlock(content=d.get("content", ""), language=d.get("language"))
    if node_type == "page_break":
        return PageBreak()
    if node_type == "line_break":
        return LineBreak()
    # Unknown → degrade to paragraph with text
    return Paragraph(content=[Text(text=d.get("text", ""))])
