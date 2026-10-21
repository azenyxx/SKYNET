import unittest
from runtime import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(next_status("created", "approve"), "ready")

    def test_boundary(self):
        with self.assertRaises(ValueError):
            next_status("created", "finish")
