import unittest
from pathlib import Path

from algolang.pipeline import run_source


EXAMPLES = Path(__file__).parent.parent / "examples"


class AlgorithmExampleTests(unittest.TestCase):
    def assert_example(self, name: str, expected: list[str]) -> None:
        path = EXAMPLES / name
        output: list[str] = []
        run_source(path.read_text(encoding="utf-8"), str(path), output.append)
        self.assertEqual(output, expected)

    def test_dynamic_programming(self):
        self.assert_example("dynamic_programming.algo", ["2"])

    def test_dijkstra(self):
        self.assert_example("dijkstra.algo", ["[0, 3, 1, 4, 7]"])

    def test_floyd_warshall(self):
        self.assert_example(
            "floyd_warshall.algo",
            ["[[0, 5, 8, 9], [99999, 0, 3, 4], [99999, 99999, 0, 1], [99999, 99999, 99999, 0]]"],
        )

    def test_bfs(self):
        self.assert_example("bfs.algo", ["[0, 1, 2, 3, 4, 5]"])

    def test_heap(self):
        self.assert_example("heap.algo", ["2", "9", "[1, 150]"])


if __name__ == "__main__": unittest.main()

