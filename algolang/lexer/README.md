# AlgoLang lexer

The lexer is the first stage of the AlgoLang execution pipeline. It reads raw
`.algo` source text from left to right and produces a sequence of `Token`
objects for the parser. Every token contains its kind, original source text,
optional literal value, and source span.

## Processing flow

```text
source text
    -> SourceCursor tracks characters and locations
    -> Lexer chooses the matching token rule
    -> literal scanners consume strings, numbers, and identifiers
    -> Token values with SourceSpan metadata
    -> parser
```

Comments and horizontal whitespace are consumed without producing tokens.
Newlines are emitted because the parser uses them as statement separators. An
`EOF` token is always appended after the source has been scanned.

## Module map

| Module | Responsibility |
|---|---|
| `__init__.py` | Stable public exports: `Lexer` and `KEYWORDS` |
| `scanner.py` | Main scan loop, character dispatch, and token emission |
| `cursor.py` | Character navigation, line/column tracking, spans, and errors |
| `literals.py` | Strings and escapes, numeric literals, and identifiers |
| `vocabulary.py` | Keywords, single-character tokens, and supported escapes |

Keeping source movement in `SourceCursor` means token rules do not need to
manually maintain offsets, lines, or columns. Multi-character values live in
`literals.py`, while `Lexer` remains responsible for deciding which rule to
apply and for emitting the final token stream.

## Public API

Callers should import from the package, not its internal modules:

```python
from algolang.lexer import Lexer

tokens = Lexer("value = 42", "example.algo").scan_tokens()
```

The package layout preserves the same import used before the lexer was split
into modules.

## Adding lexical syntax

When adding or changing a token:

1. Add its `TokenKind` in `algolang/tokens.py`.
2. Add fixed vocabulary to `vocabulary.py`, or add dispatch logic to `scanner.py`.
3. Put multi-character scanning logic in `literals.py` when appropriate.
4. Preserve cursor movement through `SourceCursor` so spans remain correct.
5. Add focused coverage to the matching `tests/lexer/test_*.py` module and an
   end-to-end case to `tests/lexer/test_integration.py` when appropriate.
6. Update `docs/language-design.md` and the VS Code grammar when syntax changes.

Lexer failures should call `SourceCursor.error()`. It raises `LexerError` with
the current token span and complete source text, allowing educational
diagnostics to show the filename, line, column, and offending source line.

## Verification

Run the focused tests while working on the lexer:

```sh
make test-lexer
```

Before opening a pull request, run the complete suite:

```sh
make test
```
