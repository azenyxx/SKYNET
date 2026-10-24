import unittest
from planning import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(plan_order({"b": ("a",), "a": ()}), ["a", "b"])

    def test_boundary(self):
        with self.assertRaises(ValueError):
            plan_order({"a": ("b",), "b": ("a",)})
