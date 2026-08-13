"""Source navigation and location tracking for the lexer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NoReturn

from ..errors import LexerError
from ..source import SourceLocation, SourceSpan


@dataclass(slots=True)
class SourceCursor:
    """Move through source text while retaining the current token's span."""

    source: str
    filename: str
    start: int = field(init=False, default=0)
    current: int = field(init=False, default=0)
    line: int = field(init=False, default=1)
    column: int = field(init=False, default=1)
    start_line: int = field(init=False, default=1)
    start_column: int = field(init=False, default=1)

    def begin_token(self) -> None:
        self.start = self.current
        self.start_line = self.line
        self.start_column = self.column

    def advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def match(self, expected: str) -> bool:
        if self.at_end() or self.source[self.current] != expected:
            return False
        self.advance()
        return True

    def peek(self) -> str:
        return "\0" if self.at_end() else self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def at_end(self) -> bool:
        return self.current >= len(self.source)

    def text(self) -> str:
        return self.source[self.start:self.current]

    def location(self) -> SourceLocation:
        return SourceLocation(self.filename, self.current, self.line, self.column)

    def span(self) -> SourceSpan:
        start = SourceLocation(
            self.filename,
            self.start,
            self.start_line,
            self.start_column,
        )
        return SourceSpan(start, self.location())

    def error(self, message: str) -> NoReturn:
        raise LexerError(message, self.span(), self.source)
