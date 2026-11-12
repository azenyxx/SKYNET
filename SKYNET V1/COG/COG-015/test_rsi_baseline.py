from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_frozen(self):
  from cognitive_rsi_baseline import validate_baseline
  b=freeze('n','s','RESOURCE');self.assertEqual(validate_baseline(b),b)
  with self.assertRaises(RSIError):validate_baseline(replace(b,fixture_commitment=H))
 def test_namespace(self):
  from cognitive_rsi_candidate import validate_candidate
  s=session()
  with self.assertRaises(RSIError):validate_candidate(s.baseline,replace(s.candidate,namespace='other'))
