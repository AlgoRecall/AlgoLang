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


if __name__ == "__main__":
    unittest.main()
