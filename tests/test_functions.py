import unittest

from algolang.errors import SemanticError, TypeCheckError
from algolang.pipeline import compile_source, run_source


class FunctionTests(unittest.TestCase):
    def output(self, source: str):
        values = []
        run_source(source, "functions.algo", values.append)
        return values

    def test_typed_function_and_recursion(self):
        source = """
fn fib(n: int) -> int {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
print(fib(8))
"""
        self.assertEqual(self.output(source), ["21"])

    def test_arrays_as_parameters_and_returns(self):
        source = """
fn firstTwo(values: [int]) -> [int] {
    return [values[0], values[1]]
}
print(firstTwo([4, 7, 9]))
"""
        self.assertEqual(self.output(source), ["[4, 7]"])

    def test_argument_type_and_arity_are_checked(self):
        source = "fn add(a: int, b: int) -> int { return a + b }\n"
        with self.assertRaises(TypeCheckError): compile_source(source + 'print(add(1, "x"))')
        with self.assertRaises(TypeCheckError): compile_source(source + "print(add(1))")

    def test_non_null_function_must_return_on_all_paths(self):
        with self.assertRaises(TypeCheckError) as context:
            compile_source("fn f(x: int) -> int { if x > 0 { return x } }")
        self.assertIn("may finish without returning int", context.exception.render())

    def test_null_function_can_return_without_value(self):
        self.assertEqual(self.output('fn greet() -> null { print("hi")\nreturn }\ngreet()'), ["hi"])

    def test_nested_functions_are_rejected(self):
        with self.assertRaises(SemanticError):
            compile_source("fn outer() -> null { fn inner() -> null { return }\nreturn }")


if __name__ == "__main__": unittest.main()

