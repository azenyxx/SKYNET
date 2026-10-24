import unittest
from qualification import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(qualify(5, 0, 5), "local_pass")

    def test_boundary(self):
        self.assertEqual(qualify(5, 1, 5), "partial")
