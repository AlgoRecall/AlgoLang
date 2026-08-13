import unittest

from algolang.errors import SemanticError, TypeCheckError
from algolang.pipeline import compile_source, run_source


class ControlFlowTests(unittest.TestCase):
    def run_program(self, source: str):
        output = []
        environment = run_source(source, "flow.algo", output.append)
        return output, environment

    def test_if_else_and_while(self):
        output, environment = self.run_program(
            "n = 5\nresult = 1\n"
            "while n > 1 {\n result = result * n\n n = n - 1\n}\n"
            'if result == 120 { print("yes") } else { print("no") }'
        )
        self.assertEqual(output, ["yes"])
        self.assertEqual(environment.values["result"], 120)

    def test_for_enumeration_break_and_continue(self):
        output, _ = self.run_program(
            "sum = 0\n"
            "for i, value in range(10) {\n"
            " if value % 2 == 0 { continue }\n"
            " if value > 5 { break }\n"
            " sum = sum + value\n"
            "}\nprint(sum)"
        )
        self.assertEqual(output, ["9"])

    def test_else_if(self):
        output, _ = self.run_program(
            'x = 2\nif x == 1 { print("one") } else if x == 2 { print("two") } else { print("many") }'
        )
        self.assertEqual(output, ["two"])

    def test_break_and_return_context_are_semantic_errors(self):
        with self.assertRaises(SemanticError): compile_source("break")
        with self.assertRaises(SemanticError): compile_source("return 1")

    def test_condition_must_be_bool(self):
        with self.assertRaises(TypeCheckError) as context:
            compile_source("if 1 { print(1) }")
        self.assertIn("if condition must be bool", context.exception.render())

    def test_block_local_does_not_escape(self):
        with self.assertRaises(TypeCheckError):
            compile_source("if true { local = 1 }\nprint(local)")


if __name__ == "__main__": unittest.main()
