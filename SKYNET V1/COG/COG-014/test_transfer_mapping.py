from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_forgery(self):
  from cognitive_transfer_mapping import validate_mapping
  a,b=pair();m=discover(a,b).mapping
  with self.assertRaises(TransferError):validate_mapping(a,b,replace(m,target_ids=('x','x','z')))
 def test_namespace(self):
  a,b=pair()
  with self.assertRaises(TransferError):discover(a,replace(b,namespace='other'))
 def test_role(self):
  a,b=pair();b=replace(b,entities=(DomainEntityV1('x','STATE'),)+b.entities[1:])
  with self.assertRaises(TransferError):discover(a,b)
