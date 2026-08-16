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
        """Mark the current position as the start of the next token."""
        self.start = self.current
        self.start_line = self.line
        self.start_column = self.column

    def advance(self) -> str:
        """Consume one character and update offset, line, and column state."""
        char = self.source[self.current]
        self.current += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def match(self, expected: str) -> bool:
        """Consume an expected character when it appears next."""
        if self.at_end() or self.source[self.current] != expected:
            return False
        self.advance()
        return True

    def peek(self) -> str:
        """Return the current character without consuming it."""
        return "\0" if self.at_end() else self.source[self.current]

    def peek_next(self) -> str:
        """Return the character after the current one without consuming it."""
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def at_end(self) -> bool:
        """Return whether all source characters have been consumed."""
        return self.current >= len(self.source)

    def text(self) -> str:
        """Return source text from the current token start to the cursor."""
        return self.source[self.start:self.current]

    def location(self) -> SourceLocation:
        """Return the current filename, offset, line, and column."""
        return SourceLocation(self.filename, self.current, self.line, self.column)

    def span(self) -> SourceSpan:
        """Return the source span from the token start to the cursor."""
        start = SourceLocation(
            self.filename,
            self.start,
            self.start_line,
            self.start_column,
        )
        return SourceSpan(start, self.location())

    def error(self, message: str) -> NoReturn:
        """Raise a lexer error spanning the current token text."""
        raise LexerError(message, self.span(), self.source)
