import unittest

from algolang.errors import LexerError
from algolang.lexer import Lexer
from algolang.tokens import TokenKind


class LexerTests(unittest.TestCase):
    def test_tokenizes_literals_operators_keywords_and_locations(self):
        tokens = Lexer('value = 12 + 3.5\nprint("ok")', "sample.algo").scan_tokens()
        self.assertEqual(
            [token.kind for token in tokens],
            [
                TokenKind.IDENTIFIER, TokenKind.EQUAL, TokenKind.INTEGER,
                TokenKind.PLUS, TokenKind.FLOAT, TokenKind.NEWLINE,
                TokenKind.PRINT, TokenKind.LEFT_PAREN, TokenKind.STRING,
                TokenKind.RIGHT_PAREN, TokenKind.EOF,
            ],
        )
        self.assertEqual(tokens[0].span.start.line, 1)
        self.assertEqual(tokens[0].span.start.column, 1)
        self.assertEqual(tokens[6].span.start.line, 2)
        self.assertEqual(tokens[6].span.start.column, 1)
        self.assertEqual(tokens[2].literal, 12)
        self.assertEqual(tokens[4].literal, 3.5)

    def test_decodes_string_escapes_and_ignores_comments(self):
        tokens = Lexer('x = "a\\n\\t\\\"b" // note\n').scan_tokens()
        string = next(token for token in tokens if token.kind is TokenKind.STRING)
        self.assertEqual(string.literal, 'a\n\t"b')

    def test_reports_unexpected_character_with_source(self):
        with self.assertRaises(LexerError) as context:
            Lexer("x = @", "bad.algo").scan_tokens()
        rendered = context.exception.render()
        self.assertIn("bad.algo:1:5", rendered)
        self.assertIn("unexpected character '@'", rendered)
        self.assertIn("1 | x = @", rendered)


if __name__ == "__main__":
    unittest.main()

