import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).parent.parent
PACKAGE = ROOT / "algolang"


class ProductionDocumentationTests(unittest.TestCase):
    def test_python_modules_classes_and_functions_have_docstrings(self):
        missing: list[str] = []

        for path in sorted(PACKAGE.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            relative = path.relative_to(ROOT)
            if ast.get_docstring(tree) is None:
                missing.append(f"{relative}: module")

            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    if ast.get_docstring(node) is None:
                        missing.append(f"{relative}:{node.lineno}: {node.name}")

        self.assertEqual(missing, [], "Missing production docstrings:\n" + "\n".join(missing))

    def test_function_docstrings_describe_parameters_and_returns(self):
        incomplete: list[str] = []

        for path in sorted(PACKAGE.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            relative = path.relative_to(ROOT)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                docstring = ast.get_docstring(node) or ""
                parameters = [
                    argument.arg
                    for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
                    if argument.arg not in {"self", "cls"}
                ]
                if node.args.vararg is not None:
                    parameters.append(node.args.vararg.arg)
                if node.args.kwarg is not None:
                    parameters.append(node.args.kwarg.arg)
                if parameters and "Args:" not in docstring:
                    incomplete.append(f"{relative}:{node.lineno}: {node.name} missing Args")
                if "Returns:" not in docstring:
                    incomplete.append(f"{relative}:{node.lineno}: {node.name} missing Returns")

        self.assertEqual(
            incomplete,
            [],
            "Incomplete function contracts:\n" + "\n".join(incomplete),
        )


if __name__ == "__main__":
    unittest.main()
