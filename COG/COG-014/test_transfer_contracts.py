from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_roundtrip(self):
  s=session();self.assertEqual(parse(TransferSessionV1,canonical(s)),s)
 def test_unknown(self):
  d=__import__('json').loads(canonical(pair()[0]));d['authority']=True
  with self.assertRaises(TransferError):parse(DomainSchemaV1,canonical(d))
 def test_trust(self):
  with self.assertRaises(TransferError):replace(pair()[0],trust='VERIFIED')
 def test_bound(self):
  with self.assertRaises(TransferError):replace(pair()[0],entities=pair()[0].entities*3)
