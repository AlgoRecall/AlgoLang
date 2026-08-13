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
    tokens = Lexer(source, filename).scan_tokens()
    return Parser(tokens, source).parse()


def compile_source(source: str, filename: str = "<source>") -> Program:
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
    program = compile_source(source, filename)
    return Interpreter(source, output, event_sink=event_sink).execute(program)


def trace_source(
    source: str,
    filename: str = "<source>",
    output: Callable[[str], None] = print,
) -> tuple[Environment, TraceCollector]:
    collector = TraceCollector()
    environment = run_source(source, filename, output, collector)
    return environment, collector
