"""Public deterministic tests. No private project sources or fixtures."""
import unittest
from V3.examples.paired_research_stats import paired_table, mcnemar_exact, wilson_interval, holm_adjust


class PairedResearchTests(unittest.TestCase):
    def test_paired_counts(self):
        self.assertEqual(paired_table({'a':True,'b':False,'c':True,'d':False},
                                      {'a':True,'b':True,'c':False,'d':False}), (1,1,1,1))

    def test_paired_missing_id(self):
        with self.assertRaises(ValueError): paired_table({'a':True}, {'b':True})

    def test_paired_reject_non_boolean(self):
        with self.assertRaises(TypeError): paired_table({'a':1}, {'a':True})

    def test_mcnemar_zero(self):
        self.assertEqual(mcnemar_exact(0,0),1.0)

    def test_mcnemar_extreme(self):
        self.assertAlmostEqual(mcnemar_exact(6,0),0.03125)

    def test_mcnemar_symmetric(self):
        self.assertEqual(mcnemar_exact(2,2),1.0)

    def test_wilson_zero_discordance(self):
        lo,hi=wilson_interval(0,29)
        self.assertEqual(lo,0.0)
        self.assertAlmostEqual(hi,0.1169698,places=5)

    def test_wilson_invalid(self):
        with self.assertRaises(ValueError): wilson_interval(2,1)

    def test_holm_adjust(self):
        self.assertEqual(holm_adjust([0.04,0.01,0.03]),[0.06,0.03,0.06])

    def test_holm_zero_and_one(self):
        self.assertEqual(holm_adjust([1.0,1.0,1.0]),[1.0,1.0,1.0])


if __name__ == '__main__': unittest.main()
