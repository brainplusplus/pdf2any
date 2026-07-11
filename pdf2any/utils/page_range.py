"""Page range parsing for --pages, --start, --end flags.

Supports:
    "1-5"       → pages 1 through 5 (inclusive)
    "1,3,5"     → pages 1, 3, 5
    "1-3,7,9-11" → pages 1,2,3,7,9,10,11
    "3"         → page 3 only

Pages are 1-indexed throughout pdf2any.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PageRange:
    """A resolved set of page numbers (1-indexed).

    Attributes:
        pages: Sorted list of unique page numbers. Empty means "all pages".
        explicit: True if the user explicitly specified a range.
    """

    pages: list[int] = field(default_factory=list)
    explicit: bool = False

    def select(self, total: int) -> list[int]:
        """Return the actual page numbers to process, given total pages.

        If empty (no explicit range), returns all pages 1..total.
        Filters out pages outside 1..total.
        """
        if not self.pages:
            return list(range(1, total + 1))
        return [p for p in self.pages if 1 <= p <= total]

    def is_empty(self) -> bool:
        return len(self.pages) == 0


def parse_page_range(
    spec: str | None,
    start: int | None = None,
    end: int | None = None,
) -> PageRange:
    """Parse a page range specification.

    Args:
        spec: A page range string like "1-3,5,7-9".
        start: Optional --start page number.
        end: Optional --end page number.

    Returns:
        A PageRange with sorted unique page numbers.

    Raises:
        ValueError: If the spec is malformed.
    """
    pages: set[int] = set()
    explicit = False

    if spec:
        explicit = True
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                bounds = part.split("-")
                if len(bounds) != 2:
                    raise ValueError(f"Invalid page range: '{part}'")
                try:
                    lo = int(bounds[0])
                    hi = int(bounds[1])
                except ValueError:
                    raise ValueError(f"Invalid page numbers in range: '{part}'") from None
                if lo > hi:
                    lo, hi = hi, lo
                pages.update(range(lo, hi + 1))
            else:
                try:
                    pages.add(int(part))
                except ValueError:
                    raise ValueError(f"Invalid page number: '{part}'") from None

    # --start / --end overrides or supplements
    if start is not None or end is not None:
        explicit = True
        s = start or 1
        e = end or 999999  # unbounded end
        if s > e:
            s, e = e, s
        if not spec:
            # If only --start/--end given (no --pages), use them as the range
            pages.update(range(s, e + 1))
        else:
            # Intersect: keep only pages within start..end
            pages = {p for p in pages if s <= p <= e}

    return PageRange(pages=sorted(pages), explicit=explicit)
