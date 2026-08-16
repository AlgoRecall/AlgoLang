"""Public helpers that compose lexing, parsing, checking, and execution."""

from __future__ import annotations

from collections.abc import Callable

from .ast_nodes import Program
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .runtime import Environment
from .semantic import SemanticAnalyzer
from .tracing import EventSink, TraceCollector
from .type_checker import TypeChecker


def parse_source(source: str, filename: str = "<source>") -> Program:
    """Tokenize and parse source text into an abstract syntax tree."""
    tokens = Lexer(source, filename).scan_tokens()
    return Parser(tokens, source).parse()


def compile_source(source: str, filename: str = "<source>") -> Program:
    """Parse and statically validate source text before execution."""
    program = parse_source(source, filename)
    SemanticAnalyzer(source).analyze(program)
    TypeChecker(source).check(program)
    return program


def run_source(
    source: str,
    filename: str = "<source>",
    output: Callable[[str], None] = print,
    event_sink: EventSink | None = None,
) -> Environment:
    """Compile and execute source text, returning its runtime environment."""
    program = compile_source(source, filename)
    return Interpreter(source, output, event_sink=event_sink).execute(program)


def trace_source(
    source: str,
    filename: str = "<source>",
    output: Callable[[str], None] = print,
) -> tuple[Environment, TraceCollector]:
    """Execute source text while collecting structured trace events."""
    collector = TraceCollector()
    environment = run_source(source, filename, output, collector)
    return environment, collector
