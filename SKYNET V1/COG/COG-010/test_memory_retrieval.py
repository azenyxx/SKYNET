from test_memory_contracts import Fixture,record,unittest,replace,MemoryErrorV1,Path,MemoryStore,asdict,canonical
from cognitive_memory_contracts import *
from cognitive_memory_retrieval import retrieve
class RetrievalTests(Fixture,unittest.TestCase):
 def q(self,ns='n',now=5):return retrieve(self.s,MemoryQueryV1(ns,'s',10,now,'UNVERIFIED'))
 def test_determinism(self):self.active();self.assertEqual(self.q(),self.q())
 def test_namespace(self):self.active();self.assertEqual(self.q('other').records,())
 def test_conflict(self):self.active();self.active(record('m2','other'));r=self.q();self.assertEqual(r.records,());self.assertEqual(len(r.conflicts),1)
 def test_revoked(self):self.active();self.s.transition('m',2,'REVOKED',5);self.assertEqual(self.q().records,())
 def test_expired(self):self.active();self.assertEqual(self.q(now=100).records,())
 def test_no_verified(self):self.active();self.assertEqual(retrieve(self.s,MemoryQueryV1('n','s',1,5,'VERIFIED')).records,())
