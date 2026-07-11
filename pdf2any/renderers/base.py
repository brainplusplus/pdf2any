"""Base renderer abstract class.

All IR-based renderers inherit from ``Renderer`` and implement ``render()``.
The ``is_binary`` property distinguishes text from binary output (binary
formats like docx/png use backends, not renderers, but the registry
unifies them under the same interface).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pdf2any.ir import IRDocument


class Renderer(ABC):
    """Abstract base class for all IR-based renderers.

    Subclasses implement ``render()`` to produce format-specific output.
    """

    @property
    @abstractmethod
    def is_binary(self) -> bool:
        """Whether this renderer produces binary output (vs text)."""

    @abstractmethod
    def render(
        self,
        doc: IRDocument,
        *,
        standalone: bool = False,
        pretty: bool = False,
    ) -> str | bytes:
        """Render an IRDocument to the target format.

        Args:
            doc: The IR document to render.
            standalone: Whether to produce a standalone document
                        (e.g. full HTML with <html> wrapper).
            pretty: Whether to pretty-print/indent the output.

        Returns:
            Rendered content as str (text formats) or bytes (binary formats).
        """
