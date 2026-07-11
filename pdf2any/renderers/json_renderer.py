"""JSON renderer — exports the raw IR as structured JSON.

This is the ``-t json`` format. It serializes the full IRDocument
(including ir_version, metadata, pages, and children) to JSON.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pdf2any.renderers.base import Renderer

if TYPE_CHECKING:
    from pdf2any.ir import IRDocument


class JSONRenderer(Renderer):
    """Render IR to raw JSON (the IR itself, serialized)."""

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
        """Render the IR document to a JSON string.

        Args:
            doc: The IR document.
            standalone: Unused (JSON is always self-contained).
            pretty: If True, indent with 2 spaces.
        """
        data = doc.to_dict()
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
