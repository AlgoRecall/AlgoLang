"""Source-aware diagnostics for every AlgoLang pipeline stage."""

from __future__ import annotations

from .source import SourceSpan


class AlgoError(Exception):
    """Base exception for source-aware AlgoLang diagnostics."""
    category = "Error"

    def __init__(self, message: str, span: SourceSpan, source: str):
        """Initialize a diagnostic with its message, source span, and source text.

        Args:
            message (str): Diagnostic message presented to the user.
            span (SourceSpan): Source range associated with the value or diagnostic.
            source (str): AlgoLang source text.

        Returns:
            None: No value is returned.
        """
        super().__init__(message)
        self.message = message
        self.span = span
        self.source = source

    def render(self) -> str:
        """Render the diagnostic with location, source line, and caret markers.

        Returns:
            str: The resulting text.
        """
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
    """Report a lexer failure with source context."""
    category = "Lexical error"


class ParseError(AlgoError):
    """Report a parse failure with source context."""
    category = "Parse error"


class SemanticError(AlgoError):
    """Report a semantic failure with source context."""
    category = "Semantic error"


class TypeCheckError(AlgoError):
    """Report a type check failure with source context."""
    category = "Type error"


class RuntimeError(AlgoError):
    """Report a runtime failure with source context."""
    category = "Runtime error"
