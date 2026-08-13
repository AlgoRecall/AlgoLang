import unittest

from algolang.errors import LexerError
from algolang.lexer import Lexer
from algolang.tokens import TokenKind


class LexerScannerTests(unittest.TestCase):
    def test_scans_single_and_multi_character_operators(self):
        tokens = Lexer("+ - -> = == != < <= > >= /", "operators.algo").scan_tokens()

        self.assertEqual(
            [token.kind for token in tokens],
            [
                TokenKind.PLUS,
                TokenKind.MINUS,
                TokenKind.ARROW,
                TokenKind.EQUAL,
                TokenKind.EQUAL_EQUAL,
                TokenKind.BANG_EQUAL,
                TokenKind.LESS,
                TokenKind.LESS_EQUAL,
                TokenKind.GREATER,
                TokenKind.GREATER_EQUAL,
                TokenKind.SLASH,
                TokenKind.EOF,
            ],
        )

    def test_skips_comments_but_preserves_the_following_newline(self):
        tokens = Lexer("value // explanation\nnext").scan_tokens()

        self.assertEqual(
            [token.kind for token in tokens],
            [
                TokenKind.IDENTIFIER,
                TokenKind.NEWLINE,
                TokenKind.IDENTIFIER,
                TokenKind.EOF,
            ],
        )
        self.assertEqual(tokens[1].lexeme, "\n")
        self.assertEqual(tokens[-1].span.start, tokens[-1].span.end)

    def test_rejects_bang_as_a_standalone_negation_operator(self):
        with self.assertRaisesRegex(LexerError, "use 'not' for negation"):
            Lexer("!value").scan_tokens()


if __name__ == "__main__":
    unittest.main()
