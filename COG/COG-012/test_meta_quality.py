from meta_test_helpers import *
from cognitive_meta_quality import evaluate_quality
class QualityTests(unittest.TestCase):
 def test_unknown_correctness(self):self.assertEqual(evaluate_quality(trace(),budget()).factual_correctness,'UNKNOWN')
 def test_constraint(self):self.assertIn('VALIDATOR_REJECTION',evaluate_quality(trace(change=('PLAN_RESULT','REJECTED')),budget()).constraint_violations)
