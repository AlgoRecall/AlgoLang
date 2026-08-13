from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceLocation:
    filename: str
    offset: int
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class SourceSpan:
    start: SourceLocation
    end: SourceLocation

    @classmethod
    def covering(cls, first: "SourceSpan", last: "SourceSpan") -> "SourceSpan":
        return cls(first.start, last.end)

