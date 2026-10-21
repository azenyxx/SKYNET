import unittest
from supervision import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(valid_transition("ready", "running", True), True)

    def test_boundary(self):
        self.assertEqual(valid_transition("completed", "running", True), False)
