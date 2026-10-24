import unittest
from collaboration import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(assign({"b": {"audit"}, "a": {"audit"}}, "audit"), "a")

    def test_boundary(self):
        self.assertEqual(assign({"a": {"read"}}, "audit"), None)
