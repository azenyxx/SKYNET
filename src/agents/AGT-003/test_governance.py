import unittest
from governance import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(authorize({"read"}, {"read", "write"}), True)

    def test_boundary(self):
        self.assertEqual(authorize({"write"}, {"read"}), False)
