from test_memory_contracts import Fixture,record,unittest,replace,MemoryErrorV1,Path,MemoryStore,asdict,canonical
from cognitive_memory_contracts import *
from cognitive_memory_consolidation import propose_consolidation
class ConsolidationTests(Fixture,unittest.TestCase):
 def test_lineage(self):
  self.active();self.active(record('m2'));old=self.s.snapshot();p=propose_consolidation(self.s,'n',('m2','m'));self.assertEqual(len(p.source_commitments),2);self.assertEqual(old,self.s.snapshot());self.assertEqual(p.status,'PROPOSAL_ONLY')
 def test_conflict_rejected(self):
  self.active();self.active(record('m2','other'))
  with self.assertRaises(MemoryErrorV1):propose_consolidation(self.s,'n',('m','m2'))
