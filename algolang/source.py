"""Source locations and spans shared by syntax nodes and diagnostics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """Represent a source location."""
    filename: str
    offset: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Represent a source span."""
    start: SourceLocation
    end: SourceLocation

    @classmethod
    def covering(cls, first: "SourceSpan", last: "SourceSpan") -> "SourceSpan":
        """Return a span extending from the first span through the last."""
        return cls(first.start, last.end)
