from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_advisory(self):self.assertFalse(session().candidate.executable)
 def test_refinement(self):
  b=freeze('n','s','ACCURACY');o=observe(b);first=propose(b,o);second=propose(b,o,'MEMO',first);self.assertEqual(second.parent_commitment,first.commitment);self.assertEqual(second.depth,1)
  with self.assertRaises(RSIError):propose(b,o,'FAST',second)
