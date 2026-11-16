from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_recommendation_only(self):
  d=session().decision;self.assertEqual(d.action,'RECOMMEND_FOR_HUMAN_REVIEW');self.assertFalse(d.production_authorized)
 def test_regression_reject(self):self.assertEqual(session('ACCURACY').decision.action,'REJECT')
 def test_stop(self):self.assertEqual(session(action='STOP').decision.action,'STOP')
 def test_no_activation(self):
  with self.assertRaises(RSIError):replace(session().decision,action='ACTIVATE')
