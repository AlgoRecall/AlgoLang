"""Top-level token scanner for AlgoLang source code."""

from __future__ import annotations

from ..source import SourceSpan
from ..tokens import Token, TokenKind
from .cursor import SourceCursor
from .literals import scan_identifier, scan_number, scan_string
from .vocabulary import SINGLE_CHARACTER_TOKENS


class Lexer:
    """Convert AlgoLang source text into a location-aware token stream."""

    def __init__(self, source: str, filename: str = "<source>"):
        """Initialize the lexer."""
        self.cursor = SourceCursor(source, filename)
        self.tokens: list[Token] = []

    def scan_tokens(self) -> list[Token]:
        """Scan the complete source and append a final end-of-file token."""
        while not self.cursor.at_end():
            self.cursor.begin_token()
            self._scan_token()

        location = self.cursor.location()
        self.tokens.append(
            Token(TokenKind.EOF, "", None, SourceSpan(location, location))
        )
        return self.tokens

    def _scan_token(self) -> None:
        """Scan one token from the current cursor position."""
        char = self.cursor.advance()

        if char in SINGLE_CHARACTER_TOKENS:
            self._add(SINGLE_CHARACTER_TOKENS[char])
        elif char == "-":
            kind = TokenKind.ARROW if self.cursor.match(">") else TokenKind.MINUS
            self._add(kind)
        elif char == "=":
            kind = TokenKind.EQUAL_EQUAL if self.cursor.match("=") else TokenKind.EQUAL
            self._add(kind)
        elif char == "!":
            self._scan_bang()
        elif char == "<":
            kind = TokenKind.LESS_EQUAL if self.cursor.match("=") else TokenKind.LESS
            self._add(kind)
        elif char == ">":
            kind = (
                TokenKind.GREATER_EQUAL
                if self.cursor.match("=")
                else TokenKind.GREATER
            )
            self._add(kind)
        elif char == "/":
            self._scan_slash_or_comment()
        elif char == "\n":
            self._add(TokenKind.NEWLINE)
        elif char in " \r\t":
            return
        elif char == '"':
            self._add(TokenKind.STRING, scan_string(self.cursor))
        elif char.isdigit():
            kind, value = scan_number(self.cursor)
            self._add(kind, value)
        elif char.isalpha() or char == "_":
            self._add(scan_identifier(self.cursor))
        else:
            self.cursor.error(f"unexpected character {char!r}")

    def _scan_bang(self) -> None:
        """Scan the ``!=`` operator or reject unsupported bare ``!``."""
        if self.cursor.match("="):
            self._add(TokenKind.BANG_EQUAL)
            return
        self.cursor.error("expected '=' after '!'; use 'not' for negation")

    def _scan_slash_or_comment(self) -> None:
        """Scan division or consume a line comment without emitting a token."""
        if not self.cursor.match("/"):
            self._add(TokenKind.SLASH)
            return
        while self.cursor.peek() not in ("\n", "\0"):
            self.cursor.advance()

    def _add(self, kind: TokenKind, literal: object = None) -> None:
        """Append a token using the cursor's current text and source span."""
        self.tokens.append(
            Token(kind, self.cursor.text(), literal, self.cursor.span())
        )
