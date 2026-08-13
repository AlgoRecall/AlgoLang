"""Public interface for turning AlgoLang source text into tokens."""

from .scanner import Lexer
from .vocabulary import KEYWORDS

__all__ = ["KEYWORDS", "Lexer"]
