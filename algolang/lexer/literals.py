"""Scanners for values and names that span multiple characters."""

from __future__ import annotations

from ..tokens import TokenKind
from .cursor import SourceCursor
from .vocabulary import KEYWORDS, STRING_ESCAPES


def scan_string(cursor: SourceCursor) -> str:
    """Read a quoted string after its opening quote has been consumed."""

    value: list[str] = []
    while not cursor.at_end() and cursor.peek() != '"':
        char = cursor.advance()
        if char == "\n":
            cursor.error("unterminated string literal")
        if char == "\\":
            if cursor.at_end():
                cursor.error("unterminated string escape")
            escaped = cursor.advance()
            if escaped not in STRING_ESCAPES:
                cursor.error(f"unknown escape sequence '\\{escaped}'")
            value.append(STRING_ESCAPES[escaped])
        else:
            value.append(char)

    if cursor.at_end():
        cursor.error("unterminated string literal")

    cursor.advance()
    return "".join(value)


def scan_number(cursor: SourceCursor) -> tuple[TokenKind, int | float]:
    """Read an integer or a float after its first digit has been consumed."""

    while cursor.peek().isdigit():
        cursor.advance()

    kind = TokenKind.INTEGER
    if cursor.peek() == "." and cursor.peek_next().isdigit():
        kind = TokenKind.FLOAT
        cursor.advance()
        while cursor.peek().isdigit():
            cursor.advance()

    text = cursor.text()
    value = int(text) if kind is TokenKind.INTEGER else float(text)
    return kind, value


def scan_identifier(cursor: SourceCursor) -> TokenKind:
    """Read an identifier and classify reserved words as keyword tokens."""

    while cursor.peek().isalnum() or cursor.peek() == "_":
        cursor.advance()
    return KEYWORDS.get(cursor.text(), TokenKind.IDENTIFIER)
