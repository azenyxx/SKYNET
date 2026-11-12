import unittest,tempfile,json
from pathlib import Path
from dataclasses import replace
from cognitive_memory_contracts import *
from cognitive_memory_store import MemoryStore

def record(mid='m',value='v',namespace='n',trust='PROVISIONAL'):
 p=MemoryProvenanceV1('synthetic',1,'TEST_ONLY');h=commitment('Content',dict(namespace=namespace,subject='s',predicate='p',value=value))
 return MemoryRecordV1(mid,namespace,'s','p',value,1,100,5,trust,(MemoryEvidenceV1('e'+mid,h,p,False),))
class Fixture:
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'db');self.s=MemoryStore(self.path,True)
 def tearDown(self):self.s.close();self.tmp.cleanup()
 def active(self,r=None):
  r=r or record();self.s.create(r);self.s.transition(r.memory_id,0,'ADMITTED',2);self.s.transition(r.memory_id,1,'ACTIVE',3)
class Contracts(unittest.TestCase):
 def test_roundtrip(self):r=record();self.assertEqual(parse(MemoryRecordV1,canonical(r)),r)
 def test_fields(self):
  o=asdict(record());o['authority']=True
  with self.assertRaises(MemoryErrorV1):parse(MemoryRecordV1,canonical(o))
 def test_duplicate_keys(self):
  with self.assertRaises(MemoryErrorV1):parse(MemoryRecordV1,b'{"a":1,"a":2}')
 def test_size(self):
  with self.assertRaises(MemoryErrorV1):record(value='x'*4097)
 def test_query_bound(self):
  with self.assertRaises(MemoryErrorV1):MemoryQueryV1('n','s',65,5,'UNVERIFIED')
