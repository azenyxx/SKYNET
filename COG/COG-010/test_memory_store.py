from test_memory_contracts import Fixture,record,unittest,replace,MemoryErrorV1,Path,MemoryStore,asdict,canonical
from cognitive_memory_contracts import *
class StoreTests(Fixture,unittest.TestCase):
 def test_restart(self):
  self.active();old=self.s.snapshot();self.s.close();self.s=MemoryStore(self.path);self.assertEqual(old,self.s.snapshot())
 def test_duplicate(self):
  self.s.create(record());before=self.s.snapshot()
  with self.assertRaises(MemoryErrorV1):self.s.create(record())
  self.assertEqual(before,self.s.snapshot())
 def test_stale(self):
  self.active()
  with self.assertRaises(MemoryErrorV1):self.s.transition('m',0,'REVOKED',5)
 def test_tombstone(self):
  self.active();self.s.transition('m',2,'TOMBSTONED',5)
  with self.assertRaises(MemoryErrorV1):self.s.transition('m',3,'ACTIVE',6)
 def test_retention(self):
  self.active()
  with self.assertRaises(MemoryErrorV1):self.s.transition('m',2,'TOMBSTONED',4)
 def test_immutable_history(self):
  self.active()
  import sqlite3
  with self.assertRaises(sqlite3.IntegrityError):self.s.db.execute('DELETE FROM revisions')

class PerformanceTests(unittest.TestCase):
 def test_measured_storage_sizes(self):
  import time,json,tempfile
  results=[]
  for n in (100,1000):
   with tempfile.TemporaryDirectory() as tmp:
    s=MemoryStore(str(Path(tmp)/'db'),True);rs=tuple(record('m'+str(i)) for i in range(n));t=time.perf_counter();s.create_many(rs);write=time.perf_counter()-t;t=time.perf_counter();snapshot=s.snapshot();read=time.perf_counter()-t;self.assertEqual(len(snapshot),n);s.close()
    results.append(dict(records=n,write_seconds=write,verified_snapshot_seconds=read,persisted_revisions=len(snapshot),status='PASS_STORAGE_ONLY',retrieval_precision='NOT_MEASURED',retrieval_recall='NOT_MEASURED'))
  results.append(dict(records=10000,status='NOT_TESTED',reason='bounded task budget; full semantic benchmark not implemented'))
  Path(__file__).with_name('BENCHMARK_RESULTS.json').write_text(json.dumps(dict(storage=results,learning_fixture=dict(total=2,baseline_correct=1,candidate_correct=2,scope='supplied deterministic predictions; not model learning'),trust_violations_observed=0,full_benchmark='NOT_IMPLEMENTED'),indent=2))
