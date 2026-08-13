import unittest

from algolang.ast_printer import AstPrinter
from algolang.errors import ParseError
from algolang.pipeline import compile_source


def printed(source: str) -> str:
    return AstPrinter().print(compile_source(source))


class ParserTests(unittest.TestCase):
    def test_multiplication_binds_more_tightly_than_addition(self):
        self.assertEqual(
            printed("x = 1 + 2 * 3"),
            "(program (assign x (+ (int 1) (* (int 2) (int 3)))))",
        )

    def test_grouping_overrides_precedence(self):
        self.assertEqual(
            printed("x = (1 + 2) * 3"),
            "(program (assign x (* (group (+ (int 1) (int 2))) (int 3))))",
        )

    def test_boolean_precedence(self):
        self.assertEqual(
            printed("x = 1 < 2 == true and false or true"),
            "(program (assign x (or (and (== (< (int 1) (int 2)) (bool true)) "
            "(bool false)) (bool true))))",
        )

    def test_semicolons_and_blank_lines_separate_statements(self):
        self.assertEqual(
            printed("\nx = 1; y = 2\n\nprint(x + y)\n"),
            "(program (assign x (int 1)) (assign y (int 2)) "
            "(print (+ (identifier x) (identifier y))))",
        )

    def test_newlines_can_format_grouped_expression(self):
        self.assertEqual(
            printed("x = (\n  1\n  +\n  2\n)"),
            "(program (assign x (group (+ (int 1) (int 2)))))",
        )

    def test_missing_operand_is_educational_parse_error(self):
        with self.assertRaises(ParseError) as context:
            compile_source("x = 10 +", "bad.algo")
        self.assertIn("expected expression", context.exception.render())
        self.assertIn("bad.algo:1:9", context.exception.render())


if __name__ == "__main__":
    unittest.main()
