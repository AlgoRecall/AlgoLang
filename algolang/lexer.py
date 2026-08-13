from __future__ import annotations

from .errors import LexerError
from .source import SourceLocation, SourceSpan
from .tokens import Token, TokenKind


KEYWORDS = {
    "true": TokenKind.TRUE, "false": TokenKind.FALSE, "null": TokenKind.NULL,
    "and": TokenKind.AND, "or": TokenKind.OR, "not": TokenKind.NOT,
    "in": TokenKind.IN, "print": TokenKind.PRINT, "fn": TokenKind.FN,
    "if": TokenKind.IF, "else": TokenKind.ELSE, "while": TokenKind.WHILE,
    "for": TokenKind.FOR, "break": TokenKind.BREAK,
    "continue": TokenKind.CONTINUE, "return": TokenKind.RETURN,
}


class Lexer:
    def __init__(self, source: str, filename: str = "<source>"):
        self.source = source
        self.filename = filename
        self.start = self.current = 0
        self.line = self.start_line = 1
        self.column = self.start_column = 1
        self.tokens: list[Token] = []

    def scan_tokens(self) -> list[Token]:
        while not self._at_end():
            self.start, self.start_line, self.start_column = self.current, self.line, self.column
            self._scan_token()
        location = self._location()
        self.tokens.append(Token(TokenKind.EOF, "", None, SourceSpan(location, location)))
        return self.tokens

    def _scan_token(self) -> None:
        char = self._advance()
        single = {
            "+": TokenKind.PLUS, "*": TokenKind.STAR, "%": TokenKind.PERCENT,
            "(": TokenKind.LEFT_PAREN, ")": TokenKind.RIGHT_PAREN,
            "{": TokenKind.LEFT_BRACE, "}": TokenKind.RIGHT_BRACE,
            "[": TokenKind.LEFT_BRACKET, "]": TokenKind.RIGHT_BRACKET,
            ",": TokenKind.COMMA, ":": TokenKind.COLON, ".": TokenKind.DOT,
            ";": TokenKind.SEMICOLON,
        }
        if char in single:
            self._add(single[char])
        elif char == "-":
            self._add(TokenKind.ARROW if self._match(">") else TokenKind.MINUS)
        elif char == "=":
            self._add(TokenKind.EQUAL_EQUAL if self._match("=") else TokenKind.EQUAL)
        elif char == "!":
            if self._match("="):
                self._add(TokenKind.BANG_EQUAL)
            else:
                self._error("expected '=' after '!'; use 'not' for negation")
        elif char == "<":
            self._add(TokenKind.LESS_EQUAL if self._match("=") else TokenKind.LESS)
        elif char == ">":
            self._add(TokenKind.GREATER_EQUAL if self._match("=") else TokenKind.GREATER)
        elif char == "/":
            if self._match("/"):
                while self._peek() not in ("\n", "\0"):
                    self._advance()
            else:
                self._add(TokenKind.SLASH)
        elif char == "\n":
            self._add(TokenKind.NEWLINE)
        elif char in " \r\t":
            return
        elif char == '"':
            self._string()
        elif char.isdigit():
            self._number()
        elif char.isalpha() or char == "_":
            self._identifier()
        else:
            self._error(f"unexpected character {char!r}")

    def _string(self) -> None:
        value: list[str] = []
        escapes = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}
        while not self._at_end() and self._peek() != '"':
            char = self._advance()
            if char == "\n":
                self._error("unterminated string literal")
            if char == "\\":
                if self._at_end():
                    self._error("unterminated string escape")
                escaped = self._advance()
                if escaped not in escapes:
                    self._error(f"unknown escape sequence '\\{escaped}'")
                value.append(escapes[escaped])
            else:
                value.append(char)
        if self._at_end():
            self._error("unterminated string literal")
        self._advance()
        self._add(TokenKind.STRING, "".join(value))

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()
        kind = TokenKind.INTEGER
        if self._peek() == "." and self._peek_next().isdigit():
            kind = TokenKind.FLOAT
            self._advance()
            while self._peek().isdigit():
                self._advance()
        text = self.source[self.start:self.current]
        self._add(kind, int(text) if kind is TokenKind.INTEGER else float(text))

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[self.start:self.current]
        self._add(KEYWORDS.get(text, TokenKind.IDENTIFIER))

    def _add(self, kind: TokenKind, literal: object = None) -> None:
        self.tokens.append(Token(
            kind, self.source[self.start:self.current], literal,
            SourceSpan(SourceLocation(self.filename, self.start, self.start_line, self.start_column), self._location()),
        ))

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        if char == "\n":
            self.line, self.column = self.line + 1, 1
        else:
            self.column += 1
        return char

    def _match(self, expected: str) -> bool:
        if self._at_end() or self.source[self.current] != expected:
            return False
        self._advance()
        return True

    def _peek(self) -> str:
        return "\0" if self._at_end() else self.source[self.current]

    def _peek_next(self) -> str:
        return "\0" if self.current + 1 >= len(self.source) else self.source[self.current + 1]

    def _at_end(self) -> bool:
        return self.current >= len(self.source)

    def _location(self) -> SourceLocation:
        return SourceLocation(self.filename, self.current, self.line, self.column)

    def _error(self, message: str) -> None:
        raise LexerError(message, SourceSpan(
            SourceLocation(self.filename, self.start, self.start_line, self.start_column), self._location()
        ), self.source)

