from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_operations(self):
  b=freeze('n','s','RESOURCE')
  for op in ('eval','exec','shell','network','../secret','disable_STOP'):
   with self.assertRaises(RSIError):propose(b,observe(b),op)
 def test_depth(self):
  with self.assertRaises(RSIError):replace(session().candidate,depth=2)
 def test_budget(self):
  s=session()
  with self.assertRaises(RSIError):evaluate(s.baseline,replace(s.candidate,operation_limit=1))
