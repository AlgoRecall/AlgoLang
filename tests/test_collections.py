import unittest

from algolang.errors import RuntimeError, TypeCheckError
from algolang.pipeline import compile_source, run_source


class CollectionTests(unittest.TestCase):
    def output(self, source: str):
        values = []
        run_source(source, "collections.algo", values.append)
        return values

    def test_arrays_maps_and_sets(self):
        source = """
nums = [2, 4]
nums.push(6)
nums[1] = 5
seen = map<int, string>()
seen[5] = "five"
unique = set<int>()
unique.add(6)
print(nums)
print(seen[5])
print(5 in seen)
print(6 in unique)
print(len(nums))
"""
        self.assertEqual(self.output(source), ["[2, 5, 6]", "five", "true", "true", "3"])

    def test_stack_queue_and_deque(self):
        source = """
s = stack<int>()
s.push(1)
s.push(2)
q = queue<string>()
q.enqueue("a")
q.enqueue("b")
d = deque<int>()
d.push_front(2)
d.push_front(1)
d.push_back(3)
print(s.pop())
print(q.dequeue())
print(d.pop_front())
print(d.pop_back())
"""
        self.assertEqual(self.output(source), ["2", "a", "1", "3"])

    def test_min_and_max_heaps(self):
        source = """
low = minheap<int>()
high = maxheap<int>()
for value in [7, 2, 9] {
 low.push(value)
 high.push(value)
}
print(low.pop())
print(high.pop())
"""
        self.assertEqual(self.output(source), ["2", "9"])

    def test_heap_supports_comparable_array_entries(self):
        source = """
frontier = minheap<[int]>()
frontier.push([7, 1])
frontier.push([2, 3])
frontier.push([2, 1])
print(frontier.pop())
print(frontier.pop())
"""
        self.assertEqual(self.output(source), ["[2, 1]", "[2, 3]"])

    def test_generic_collection_rejects_wrong_element(self):
        with self.assertRaises(TypeCheckError) as context:
            compile_source('s = stack<int>()\ns.push("wrong")')
        self.assertIn("expected int, got string", context.exception.render())

    def test_empty_pop_is_runtime_error(self):
        with self.assertRaises(RuntimeError) as context:
            self.output("s = stack<int>()\nprint(s.pop())")
        self.assertIn("empty stack", context.exception.render())


if __name__ == "__main__": unittest.main()
