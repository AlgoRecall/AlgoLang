import unittest

from algolang.errors import RuntimeError, TypeCheckError
from algolang.pipeline import run_source


class InterpreterTests(unittest.TestCase):
    def run_program(self, source: str):
        output = []
        environment = run_source(source, "test.algo", output.append)
        return output, environment

    def test_assignment_arithmetic_and_print(self):
        output, environment = self.run_program(
            "x = 10\ny = 20\nresult = x + y * 2\nprint(result)"
        )
        self.assertEqual(output, ["50"])
        self.assertEqual(environment.values["result"], 50)

    def test_primitives_comparisons_and_string_concatenation(self):
        output, _ = self.run_program(
            'print(7 / 2)\nprint(7 % 2)\nprint("algo" + "lang")\n'
            "print(1 == 1.0)\nprint(true != false)\nprint(\"b\" > \"a\")"
        )
        self.assertEqual(output, ["3", "1", "algolang", "true", "true", "true"])

    def test_boolean_operators_short_circuit(self):
        output, _ = self.run_program(
            "print(false and (1 / 0 == 0))\nprint(true or (1 / 0 == 0))\nprint(not false)"
        )
        self.assertEqual(output, ["false", "true", "true"])

    def test_undefined_variable_reports_runtime_error(self):
        with self.assertRaises(TypeCheckError) as context:
            self.run_program("print(answer)")
        self.assertIn("undefined name 'answer'", context.exception.render())
        self.assertIn("test.algo:1:7", context.exception.render())

    def test_bool_is_not_a_number(self):
        with self.assertRaises(TypeCheckError) as context:
            self.run_program("x = true + 1")
        self.assertIn("requires numbers, got bool and int", context.exception.render())

    def test_boolean_operator_requires_bool(self):
        with self.assertRaises(TypeCheckError) as context:
            self.run_program("x = 1 and true")
        self.assertIn("must be bool, got int", context.exception.render())

    def test_division_by_zero_is_language_runtime_error(self):
        with self.assertRaises(RuntimeError) as context:
            self.run_program("x = 1 / 0")
        self.assertIn("division by zero", context.exception.render())


if __name__ == "__main__":
    unittest.main()
