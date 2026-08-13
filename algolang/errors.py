from __future__ import annotations

from .source import SourceSpan


class AlgoError(Exception):
    category = "Error"

    def __init__(self, message: str, span: SourceSpan, source: str):
        super().__init__(message)
        self.message = message
        self.span = span
        self.source = source

    def render(self) -> str:
        location = self.span.start
        lines = self.source.splitlines()
        line_text = lines[location.line - 1] if location.line <= len(lines) else ""
        width = max(1, self.span.end.offset - self.span.start.offset)
        if self.span.end.line != location.line:
            width = 1
        width = min(width, max(1, len(line_text) - location.column + 2))
        gutter = str(location.line)
        pointer = " " * (location.column - 1) + "^" * width
        return (
            f"{location.filename}:{location.line}:{location.column}: "
            f"{self.category}: {self.message}\n"
            f"{gutter} | {line_text}\n"
            f"{' ' * len(gutter)} | {pointer}"
        )


class LexerError(AlgoError):
    category = "Lexical error"


class ParseError(AlgoError):
    category = "Parse error"


class SemanticError(AlgoError):
    category = "Semantic error"


class TypeCheckError(AlgoError):
    category = "Type error"


class RuntimeError(AlgoError):
    category = "Runtime error"
