import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def invoke(self, command: str, source: str, *extra_args: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "program.algo"
            path.write_text(source, encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-m", "algolang", command, str(path), *extra_args],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_run_command(self):
        result = self.invoke("run", "x = 6 * 7\nprint(x)")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "42\n")
        self.assertEqual(result.stderr, "")

    def test_ast_and_check_commands(self):
        ast_result = self.invoke("ast", "x = 1 + 2")
        self.assertEqual(ast_result.returncode, 0)
        self.assertIn("(assign x (+ (int 1) (int 2)))", ast_result.stdout)
        check_result = self.invoke("check", "x = 1")
        self.assertEqual(check_result.stdout, "OK\n")

    def test_error_exit_status_and_diagnostic(self):
        result = self.invoke("run", "print(nope)")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Type error: undefined name 'nope'", result.stderr)

    def test_dryrun_command_and_watch_filter(self):
        result = self.invoke(
            "dryrun",
            "x = 0\ny = 10\nwhile x < 2 { x = x + 1 }\nprint(x)",
            "--watch", "x",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("State transitions", result.stdout)
        header = next(line for line in result.stdout.splitlines() if line.startswith("Step |"))
        self.assertIn("x", header)
        self.assertNotIn(" y", header)
        self.assertIn("Program output\n2", result.stdout)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
