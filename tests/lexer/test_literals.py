import unittest

from algolang.errors import LexerError
from algolang.lexer.cursor import SourceCursor
from algolang.lexer.literals import scan_identifier, scan_number, scan_string
from algolang.tokens import TokenKind


class LexerLiteralTests(unittest.TestCase):
    def test_scans_integer_and_float_values(self):
        integer_cursor = self._cursor_after_first_character("123")
        self.assertEqual(scan_number(integer_cursor), (TokenKind.INTEGER, 123))

        float_cursor = self._cursor_after_first_character("3.25")
        self.assertEqual(scan_number(float_cursor), (TokenKind.FLOAT, 3.25))

    def test_leaves_a_dot_without_following_digit_for_the_next_token(self):
        cursor = self._cursor_after_first_character("1.value")

        self.assertEqual(scan_number(cursor), (TokenKind.INTEGER, 1))
        self.assertEqual(cursor.peek(), ".")

    def test_distinguishes_keywords_from_identifiers(self):
        keyword_cursor = self._cursor_after_first_character("while")
        self.assertEqual(scan_identifier(keyword_cursor), TokenKind.WHILE)

        identifier_cursor = self._cursor_after_first_character("while_count2")
        self.assertEqual(scan_identifier(identifier_cursor), TokenKind.IDENTIFIER)

    def test_decodes_supported_string_escapes(self):
        cursor = self._cursor_after_first_character('"line\\n\\t\\"quote\\\\"')

        value = scan_string(cursor)

        self.assertEqual(value, 'line\n\t"quote\\')
        self.assertTrue(cursor.at_end())

    def test_rejects_unknown_escape_and_unterminated_string(self):
        unknown_escape = self._cursor_after_first_character('"bad\\q"')
        with self.assertRaisesRegex(LexerError, "unknown escape sequence"):
            scan_string(unknown_escape)

        unterminated = self._cursor_after_first_character('"missing')
        with self.assertRaisesRegex(LexerError, "unterminated string literal"):
            scan_string(unterminated)

    @staticmethod
    def _cursor_after_first_character(source: str) -> SourceCursor:
        cursor = SourceCursor(source, "literal.algo")
        cursor.begin_token()
        cursor.advance()
        return cursor


if __name__ == "__main__":
    unittest.main()
