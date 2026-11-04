import unittest
from fractions import Fraction
from skynet_public_eval.prng import DetRNG
from skynet_public_eval.stats import q6_round, wilson_q6

class PublicTests(unittest.TestCase):
    def test_deterministic_rng(self):
        a = [DetRNG(b"seed").below(100) for _ in range(2)]
        self.assertEqual(a[0], a[1])
    def test_q6_rounding(self):
        self.assertEqual(q6_round(Fraction(5, 2)), 2)
        self.assertEqual(q6_round(Fraction(7, 2)), 4)
    def test_wilson(self):
        result = wilson_q6(3, 4, 950000)
        self.assertEqual(result['k'], 3)
        self.assertEqual(result['n'], 4)

if __name__ == '__main__': unittest.main()
