"""Fixed vocabulary used by the AlgoLang lexer."""

from __future__ import annotations

from ..tokens import TokenKind


KEYWORDS: dict[str, TokenKind] = {
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "null": TokenKind.NULL,
    "and": TokenKind.AND,
    "or": TokenKind.OR,
    "not": TokenKind.NOT,
    "in": TokenKind.IN,
    "print": TokenKind.PRINT,
    "fn": TokenKind.FN,
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "for": TokenKind.FOR,
    "break": TokenKind.BREAK,
    "continue": TokenKind.CONTINUE,
    "return": TokenKind.RETURN,
}

SINGLE_CHARACTER_TOKENS: dict[str, TokenKind] = {
    "+": TokenKind.PLUS,
    "*": TokenKind.STAR,
    "%": TokenKind.PERCENT,
    "(": TokenKind.LEFT_PAREN,
    ")": TokenKind.RIGHT_PAREN,
    "{": TokenKind.LEFT_BRACE,
    "}": TokenKind.RIGHT_BRACE,
    "[": TokenKind.LEFT_BRACKET,
    "]": TokenKind.RIGHT_BRACKET,
    ",": TokenKind.COMMA,
    ":": TokenKind.COLON,
    ".": TokenKind.DOT,
    ";": TokenKind.SEMICOLON,
}

STRING_ESCAPES: dict[str, str] = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    '"': '"',
    "\\": "\\",
}
