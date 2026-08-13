import unittest

from algolang.errors import TypeCheckError
from algolang.pipeline import compile_source, run_source


class TypeCheckerTests(unittest.TestCase):
    def test_inference_and_explicit_types(self):
        compile_source("x = 1\ny: float = x\nvalues: [int] = [1, 2, 3]")

    def test_reassignment_preserves_inferred_type(self):
        with self.assertRaises(TypeCheckError) as context:
            compile_source('x = 1\nx = "changed"')
        self.assertIn("expected int, got string", context.exception.render())

    def test_heterogeneous_arrays_are_rejected(self):
        with self.assertRaises(TypeCheckError): compile_source('values = [1, "two"]')

    def test_empty_array_needs_context(self):
        with self.assertRaises(TypeCheckError): compile_source("values = []")
        compile_source("values: [int] = []")
        compile_source("fn empty() -> [int] { return [] }")

    def test_generic_arity_and_unknown_types_are_reported(self):
        with self.assertRaises(TypeCheckError): compile_source("x = map<int>()")
        with self.assertRaises(TypeCheckError): compile_source("x: mystery = 1")

    def test_integer_division_supports_algorithm_indexes(self):
        output = []
        run_source("nums = [10, 20, 30]\nmid = (len(nums) - 1) / 2\nprint(nums[mid])", output=output.append)
        self.assertEqual(output, ["20"])


if __name__ == "__main__": unittest.main()
