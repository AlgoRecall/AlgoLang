import unittest

from algolang.errors import LexerError
from algolang.lexer.cursor import SourceCursor


class SourceCursorTests(unittest.TestCase):
    def test_tracks_text_offsets_lines_columns_and_spans(self):
        cursor = SourceCursor("a\nb", "sample.algo")

        cursor.begin_token()
        self.assertEqual(cursor.peek(), "a")
        self.assertEqual(cursor.peek_next(), "\n")
        self.assertEqual(cursor.advance(), "a")
        self.assertEqual(cursor.text(), "a")
        self.assertEqual(cursor.location().line, 1)
        self.assertEqual(cursor.location().column, 2)

        self.assertEqual(cursor.advance(), "\n")
        self.assertEqual(cursor.location().line, 2)
        self.assertEqual(cursor.location().column, 1)

        span = cursor.span()
        self.assertEqual(span.start.filename, "sample.algo")
        self.assertEqual(span.start.offset, 0)
        self.assertEqual(span.end.offset, 2)

    def test_matches_only_the_expected_character(self):
        cursor = SourceCursor("=>", "operators.algo")

        self.assertFalse(cursor.match(">"))
        self.assertEqual(cursor.location().offset, 0)
        self.assertTrue(cursor.match("="))
        self.assertTrue(cursor.match(">"))
        self.assertTrue(cursor.at_end())
        self.assertEqual(cursor.peek(), "\0")
        self.assertEqual(cursor.peek_next(), "\0")

    def test_raises_location_aware_lexer_error(self):
        cursor = SourceCursor("@", "bad.algo")
        cursor.begin_token()
        cursor.advance()

        with self.assertRaises(LexerError) as context:
            cursor.error("unexpected character '@'")

        rendered = context.exception.render()
        self.assertIn("bad.algo:1:1", rendered)
        self.assertIn("unexpected character '@'", rendered)


if __name__ == "__main__":
    unittest.main()
