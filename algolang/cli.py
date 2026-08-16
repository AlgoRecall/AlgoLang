"""Command-line entry points for running and inspecting AlgoLang programs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ast_printer import AstPrinter
from .dryrun import render_dry_run
from .errors import AlgoError
from .pipeline import compile_source, parse_source, run_source, trace_source


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser for the AlgoLang CLI."""
    parser = argparse.ArgumentParser(prog="algo", description="Run and inspect AlgoLang programs")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("run", "execute a program"),
        ("ast", "print the parsed AST"),
        ("check", "parse, analyze, and type-check a program"),
    ):
        child = subparsers.add_parser(command, help=help_text)
        child.add_argument("file", type=Path)
    dryrun = subparsers.add_parser("dryrun", help="execute with a state table and call tree")
    dryrun.add_argument("file", type=Path)
    dryrun.add_argument(
        "--watch", action="append", default=[], metavar="NAME",
        help="show a variable (repeat or use comma-separated names)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the AlgoLang command-line interface and return its exit status."""
    args = build_parser().parse_args(argv)
    try:
        source = args.file.read_text(encoding="utf-8")
        filename = str(args.file)
        if args.command == "run":
            run_source(source, filename)
        elif args.command == "dryrun":
            output: list[str] = []
            _, trace = trace_source(source, filename, output.append)
            print(render_dry_run(trace, filename, output, args.watch))
        else:
            program = parse_source(source, filename) if args.command == "ast" else compile_source(source, filename)
            if args.command == "ast":
                print(AstPrinter().print(program))
            else:
                print("OK")
        return 0
    except OSError as error:
        print(f"algo: cannot read {args.file}: {error}", file=sys.stderr)
        return 2
    except AlgoError as error:
        print(error.render(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
