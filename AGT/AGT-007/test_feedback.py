import unittest
from feedback import *

class ExampleTests(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(progress(2, 4), 0.5)

    def test_boundary(self):
        with self.assertRaises(ValueError):
            progress(5, 4)
