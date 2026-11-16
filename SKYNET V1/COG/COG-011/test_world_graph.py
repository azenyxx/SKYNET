from world_test_helpers import *
from cognitive_world_graph import traverse
class GraphTests(Fixture,unittest.TestCase):
 def setup_graph(self):
  self.add(observation());self.add(observation('b',oid='o2'));self.add(observation(kind='RELATION',target='b',oid='o3'));return self.add(observation('b',kind='RELATION',target='a',oid='o4'))
 def test_cycle_safe(self):s=self.setup_graph();q=WorldQueryV1('n',P,'UNKNOWN','UNVERIFIED','a',8,64,20);self.assertEqual(traverse(s,q),('b',))
 def test_namespace(self):
  s=self.setup_graph()
  with self.assertRaises(WorldError):traverse(s,WorldQueryV1('other',P,'UNKNOWN','UNVERIFIED','a',1,1,20))
 def test_bound(self):
  with self.assertRaises(WorldError):WorldQueryV1('n',P,'UNKNOWN','UNVERIFIED','a',9,100,20)
