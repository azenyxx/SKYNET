from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_hypothesis_only(self):
  h=session().hypothesis;self.assertEqual(h.epistemic,'HYPOTHESIZED');self.assertFalse(h.executable)
 def test_prediction_not_observation(self):
  with self.assertRaises(TransferError):replace(session().evaluation.evidence[0].prediction,epistemic='OBSERVED')
