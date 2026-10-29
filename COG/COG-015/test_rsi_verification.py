from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_tamper(self):
  s=session();e=replace(s.evaluation,regressions=1)
  with self.assertRaises(RSIError):challenge(s.baseline,s.candidate,e)
 def test_false_resource(self):
  s=session();e=replace(s.evaluation,candidate_metrics=replace(s.evaluation.candidate_metrics,operations=0))
  with self.assertRaises(RSIError):challenge(s.baseline,s.candidate,e)
 def test_hidden_negative(self):
  s=session('ACCURACY');e=replace(s.evaluation,regressions=0)
  with self.assertRaises(RSIError):challenge(s.baseline,s.candidate,e)
 def test_fake_challenge(self):
  s=session('ACCURACY')
  with self.assertRaises(RSIError):decide(s.baseline,s.candidate,s.evaluation,replace(s.challenge,status='CONSISTENT'))
