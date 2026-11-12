from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_grounded(self):
  from cognitive_rsi_diagnostics import diagnose
  b=freeze('n','s','RESOURCE');self.assertEqual(diagnose(b,observe(b)).kind,'REDUNDANT_WORK')
 def test_revoked(self):
  from cognitive_rsi_diagnostics import diagnose
  b=freeze('n','s','RESOURCE')
  with self.assertRaises(RSIError):diagnose(b,replace(observe(b),revoked=True))
 def test_forged_metrics(self):
  from cognitive_rsi_diagnostics import diagnose
  b=freeze('n','s','RESOURCE');o=observe(b)
  with self.assertRaises(RSIError):diagnose(b,replace(o,metrics=replace(o.metrics,operations=1)))
