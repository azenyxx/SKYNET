from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_preserve(self):
  from cognitive_transfer_abstraction import abstract
  a=pair()[0];self.assertEqual(abstract(a).constraints,a.constraints)
 def test_missing(self):
  from cognitive_transfer_abstraction import abstract
  with self.assertRaises(TransferError):abstract(replace(pair()[0],constraints=()))
