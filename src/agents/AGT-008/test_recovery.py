import unittest
from recovery import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(recovery_advice("failed", True), "escalate_to_host")

    def test_boundary(self):
        self.assertEqual(recovery_advice("ready", False), "no_action")
