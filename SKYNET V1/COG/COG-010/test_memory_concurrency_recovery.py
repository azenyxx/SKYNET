from test_memory_contracts import Fixture,record,unittest,replace,MemoryErrorV1,Path,MemoryStore,asdict,canonical
from cognitive_memory_contracts import *
import multiprocessing,os
CTX=multiprocessing.get_context('fork')
def race(path,bar,q):
 s=MemoryStore(path)
 try:bar.wait(2);s.transition('m',2,'REVOKED',5);q.put('WIN')
 except MemoryErrorV1:q.put('REJECT')
 finally:s.close()
def crash(path):
 s=MemoryStore(path);s.db.execute('BEGIN IMMEDIATE');s.db.execute("DELETE FROM heads");os._exit(71)
class RecoveryTests(Fixture,unittest.TestCase):
 def test_concurrent_cas(self):
  self.active();bar=CTX.Barrier(2);q=CTX.Queue();ps=[CTX.Process(target=race,args=(self.path,bar,q)) for _ in range(2)]
  for p in ps:p.start()
  for p in ps:p.join(3);self.assertEqual(p.exitcode,0)
  self.assertEqual(sorted(q.get(timeout=1) for _ in ps),['REJECT','WIN']);q.close();q.join_thread();self.assertEqual(self.s.verify()[0].state,'REVOKED')
 def test_crash_rollback(self):
  self.active();old=self.s.snapshot();p=CTX.Process(target=crash,args=(self.path,));p.start();p.join(3);self.assertEqual(p.exitcode,71);self.s.close();self.s=MemoryStore(self.path);self.assertEqual(old,self.s.snapshot())
