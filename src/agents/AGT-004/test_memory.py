import unittest
from memory import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(summarize((("observation", "x"), ("observation", "y"))), {"observation": 2})

    def test_boundary(self):
        self.assertEqual(summarize(()), {})
