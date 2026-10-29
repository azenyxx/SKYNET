from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_renamed(self):
  a,b=pair();m=discover(a,b);self.assertEqual(m.mapping.target_ids,('x','y','z'))
 def test_similar_names_incompatible(self):
  a,b=pair();b=replace(a,domain_id='target',relations=a.relations+(DomainRelationV1('c','a','PRECEDES'),))
  with self.assertRaises(TransferError):discover(a,b)
 def test_search_bound(self):
  a,b=pair()
  with self.assertRaises(TransferError):discover(a,b,1)
