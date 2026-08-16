import unittest

from algolang import trace_source
from algolang.pipeline import run_source
from algolang.tracing import (
    ArrayUpdated, ConditionEvaluated, DequeUpdated, ExpressionEvaluated,
    FunctionCalled, FunctionReturned, HeapPopped, HeapPushed, LoopExitReason,
    LoopFinished, LoopIteration, LoopStarted, MapUpdated, QueueDequeued,
    QueueEnqueued, RuntimeSnapshot, SetUpdated, StackPopped, StackPushed,
    VariableChanged, VariableDeclared,
)


class TracingTests(unittest.TestCase):
    def trace(self, source: str):
        output = []
        environment, collector = trace_source(source, "trace.algo", output.append)
        return output, environment, collector

    def test_variable_events_distinguish_declaration_and_change(self):
        _, _, trace = self.trace("x = 1\nx = 2")
        declared = trace.of_type(VariableDeclared)
        changed = trace.of_type(VariableChanged)
        self.assertEqual([(event.name, event.value.value) for event in declared], [("x", 1)])
        self.assertEqual([(event.name, event.old_value.value, event.new_value.value) for event in changed], [("x", 1, 2)])
        self.assertEqual(declared[0].span.start.line, 1)
        self.assertEqual(changed[0].span.start.line, 2)
        self.assertEqual(declared[0].scope_id, changed[0].scope_id)

    def test_snapshots_do_not_change_after_mutation(self):
        _, _, trace = self.trace("values = [1]\nvalues.push(2)")
        declaration = next(event for event in trace.events if isinstance(event, VariableDeclared))
        update = next(event for event in trace.events if isinstance(event, ArrayUpdated))
        self.assertEqual(declaration.value, RuntimeSnapshot("array", (RuntimeSnapshot("int", 1),)))
        self.assertEqual(
            update.state,
            RuntimeSnapshot("array", (RuntimeSnapshot("int", 1), RuntimeSnapshot("int", 2))),
        )

    def test_expression_condition_and_loop_lifecycle(self):
        _, _, trace = self.trace("x = 0\nwhile x < 3 {\n x = x + 1\n}")
        self.assertGreater(len(trace.of_type(ExpressionEvaluated)), 0)
        conditions = trace.of_type(ConditionEvaluated)
        self.assertEqual([event.value for event in conditions], [True, True, True, False])
        started = trace.of_type(LoopStarted)
        iterations = trace.of_type(LoopIteration)
        finished = trace.of_type(LoopFinished)
        self.assertEqual(len(started), 1)
        self.assertEqual([event.iteration for event in iterations], [1, 2, 3])
        self.assertEqual(finished[0].iterations, 3)
        self.assertEqual(finished[0].reason, LoopExitReason.COMPLETED)
        self.assertEqual(started[0].loop_id, finished[0].loop_id)

    def test_loop_records_break_reason(self):
        _, _, trace = self.trace("for x in [1, 2, 3] { break }")
        finished = trace.of_type(LoopFinished)
        self.assertEqual(finished[0].iterations, 1)
        self.assertEqual(finished[0].reason, LoopExitReason.BREAK)

    def test_recursive_calls_have_unique_parented_call_ids(self):
        source = """
fn sumTo(n: int) -> int {
    if n == 0 { return 0 }
    return n + sumTo(n - 1)
}
print(sumTo(2))
"""
        output, _, trace = self.trace(source)
        calls = trace.of_type(FunctionCalled)
        returns = trace.of_type(FunctionReturned)
        self.assertEqual(output, ["3"])
        self.assertEqual([event.call_id for event in calls], [1, 2, 3])
        self.assertEqual([event.parent_call_id for event in calls], [None, 1, 2])
        self.assertEqual([event.call_id for event in returns], [3, 2, 1])
        parameter_events = [
            event for event in trace.of_type(VariableDeclared) if event.name == "n"
        ]
        self.assertEqual([event.call_id for event in parameter_events], [1, 2, 3])

    def test_array_map_and_set_mutations(self):
        source = """
values = [1]
values.push(2)
values[0] = 3
values.pop()
lookup = map<int, string>()
lookup[1] = "one"
lookup[1] = "uno"
items = set<int>()
items.add(4)
items.add(4)
items.remove(4)
"""
        _, _, trace = self.trace(source)
        arrays = trace.of_type(ArrayUpdated)
        maps = trace.of_type(MapUpdated)
        sets = trace.of_type(SetUpdated)
        self.assertEqual(len(arrays), 3)
        self.assertEqual(len({event.collection_id for event in arrays}), 1)
        self.assertEqual([event.existed for event in maps], [False, True])
        self.assertEqual([event.changed for event in sets], [True, False, True])

    def test_algorithm_collection_mutations(self):
        source = """
s = stack<int>()
s.push(1)
s.pop()
q = queue<int>()
q.enqueue(2)
q.dequeue()
d = deque<int>()
d.push_front(3)
d.pop_back()
h = minheap<int>()
h.push(4)
h.pop()
"""
        _, _, trace = self.trace(source)
        expected = (
            StackPushed, StackPopped, QueueEnqueued, QueueDequeued,
            DequeUpdated, HeapPushed, HeapPopped,
        )
        for event_type in expected:
            self.assertGreaterEqual(len(trace.of_type(event_type)), 1, event_type.__name__)
        self.assertEqual(len(trace.of_type(DequeUpdated)), 2)

    def test_custom_sink_can_observe_without_collector(self):
        class CountingSink:
            def __init__(self): self.count = 0
            def emit(self, event): self.count += 1

        sink = CountingSink()
        output = []
        run_source("x = 40 + 2\nprint(x)", output=output.append, event_sink=sink)
        self.assertEqual(output, ["42"])
        self.assertGreater(sink.count, 0)

    def test_default_execution_does_not_require_tracing(self):
        output = []
        run_source("print(6 * 7)", output=output.append)
        self.assertEqual(output, ["42"])


if __name__ == "__main__": unittest.main()
