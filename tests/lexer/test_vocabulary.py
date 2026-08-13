import unittest

from algolang.lexer import KEYWORDS
from algolang.lexer.vocabulary import SINGLE_CHARACTER_TOKENS, STRING_ESCAPES
from algolang.tokens import TokenKind


class LexerVocabularyTests(unittest.TestCase):
    def test_keywords_map_reserved_words_to_their_token_kinds(self):
        self.assertEqual(KEYWORDS["if"], TokenKind.IF)
        self.assertEqual(KEYWORDS["return"], TokenKind.RETURN)
        self.assertNotIn("algorithm", KEYWORDS)

    def test_single_character_tokens_cover_delimiters_and_operators(self):
        self.assertEqual(SINGLE_CHARACTER_TOKENS["+"], TokenKind.PLUS)
        self.assertEqual(SINGLE_CHARACTER_TOKENS["("], TokenKind.LEFT_PAREN)
        self.assertEqual(SINGLE_CHARACTER_TOKENS["}"], TokenKind.RIGHT_BRACE)

    def test_string_escape_table_contains_the_supported_escapes(self):
        self.assertEqual(
            set(STRING_ESCAPES),
            {"n", "r", "t", '"', "\\"},
        )
        self.assertEqual(STRING_ESCAPES["n"], "\n")


if __name__ == "__main__":
    unittest.main()
