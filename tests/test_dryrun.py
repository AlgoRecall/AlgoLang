import unittest

from algolang import ExecutionReplay, trace_source
from algolang.dryrun import build_call_forest, render_call_forest, render_dry_run
from algolang.tracing import VariableChanged, VariableDeclared


class DryRunTests(unittest.TestCase):
    def trace(self, source: str):
        output = []
        _, trace = trace_source(source, "solution.algo", output.append)
        return output, trace

    def test_replay_steps_forward_backward_and_seeks(self):
        _, trace = self.trace("x = 1\nx = 2")
        declaration_index = next(
            index for index, event in enumerate(trace.events)
            if isinstance(event, VariableDeclared)
        )
        change_index = next(
            index for index, event in enumerate(trace.events)
            if isinstance(event, VariableChanged)
        )
        replay = ExecutionReplay(trace)
        replay.seek(declaration_index)
        self.assertEqual(replay.visible_variables(None)["x"].value, 1)
        replay.seek(change_index)
        self.assertEqual(replay.visible_variables(None)["x"].value, 2)
        replay.step_backward()
        self.assertEqual(replay.visible_variables(None)["x"].value, 1)
        replay.reset()
        self.assertEqual(replay.position, -1)
        self.assertEqual(replay.state.variables, {})

    def test_replay_follows_mutable_variable_alias(self):
        _, trace = self.trace("values = [1]\nvalues.push(2)")
        replay = ExecutionReplay(trace)
        replay.seek(len(trace.events) - 1)
        value = replay.visible_variables(None)["values"]
        self.assertEqual([item.value for item in value.value], [1, 2])

    def test_rendered_table_filters_watched_columns(self):
        output, trace = self.trace(
            "left = 0\nright = 2\nwhile left < right { left = left + 1 }\nprint(left)"
        )
        report = render_dry_run(trace, "solution.algo", output, ["left"])
        header = next(line for line in report.splitlines() if line.startswith("Step |"))
        self.assertIn("left", header)
        self.assertNotIn("right", header)
        self.assertIn("while iteration", report)
        self.assertIn("Program output\n2", report)

    def test_comma_separated_watches_are_supported(self):
        _, trace = self.trace("left = 0\nright = 1")
        report = render_dry_run(trace, "solution.algo", watches=["left,right"])
        header = next(line for line in report.splitlines() if line.startswith("Step |"))
        self.assertIn("left", header)
        self.assertIn("right", header)

    def test_recursive_call_tree_is_reconstructed(self):
        source = """
fn fib(n: int) -> int {
    if n <= 1 { return n }
    return fib(n - 1) + fib(n - 2)
}
print(fib(3))
"""
        _, trace = self.trace(source)
        forest = build_call_forest(trace.events)
        tree = render_call_forest(forest)
        self.assertIn("fib(3) -> 2", tree)
        self.assertIn("├── fib(2) -> 1", tree)
        self.assertIn("│   ├── fib(1) -> 1", tree)
        self.assertIn("└── fib(1) -> 1", tree)

    def test_report_auto_discovers_variables(self):
        _, trace = self.trace("first = 1\nsecond = 2")
        report = render_dry_run(trace, "solution.algo")
        header = next(line for line in report.splitlines() if line.startswith("Step |"))
        self.assertIn("first", header)
        self.assertIn("second", header)


if __name__ == "__main__": unittest.main()

