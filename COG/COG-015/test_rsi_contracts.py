from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_roundtrip(self):
  s=session();self.assertEqual(parse(ImprovementSessionV1,canonical(s)),s)
 def test_trust(self):
  with self.assertRaises(RSIError):replace(session().candidate,trust='VERIFIED')
 def test_unknown(self):
  import json
  o=json.loads(canonical(session().candidate));o['code']='exec(1)'
  with self.assertRaises(RSIError):parse(ImprovementCandidateV1,canonical(o))
