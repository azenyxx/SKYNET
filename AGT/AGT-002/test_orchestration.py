import unittest
from orchestration import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(ready_tasks({"a": (), "b": ("a",)}, set()), ["a"])

    def test_boundary(self):
        with self.assertRaises(ValueError):
            ready_tasks({"b": ("missing",)}, set())
