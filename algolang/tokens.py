"""Token categories and source-spanned token values."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from .source import SourceSpan


class TokenKind(Enum):
    """Represent a token kind."""
    EOF = auto()
    NEWLINE = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    PRINT = auto()
    FN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()
    PLUS = auto()
    MINUS = auto()
    ARROW = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    COMMA = auto()
    COLON = auto()
    DOT = auto()
    SEMICOLON = auto()


@dataclass(frozen=True, slots=True)
class Token:
    """Represent a token."""
    kind: TokenKind
    lexeme: str
    literal: Any
    span: SourceSpan
