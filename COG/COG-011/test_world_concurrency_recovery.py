from world_test_helpers import *
import multiprocessing,os
CTX=multiprocessing.get_context('fork')
def write(path,e,bar,q):
 s=WorldStore(path)
 try:bar.wait(2);s.append(e);q.put('WIN')
 except WorldError:q.put('REJECT')
 finally:s.close()
def crash(path):
 s=WorldStore(path);s.db.execute('BEGIN IMMEDIATE');s.db.execute('DROP TRIGGER no_delete');s.db.execute('DELETE FROM events');os._exit(72)
class RecoveryTests(Fixture,unittest.TestCase):
 def test_race(self):
  state=self.add(observation());es=[event(state,observation(kind='ATTRIBUTE',value=str(i),oid='race'+str(i))) for i in range(2)];bar=CTX.Barrier(2);q=CTX.Queue();ps=[CTX.Process(target=write,args=(self.path,e,bar,q)) for e in es]
  for p in ps:p.start()
  for p in ps:p.join(3);self.assertEqual(p.exitcode,0)
  self.assertEqual(sorted(q.get(timeout=1) for _ in ps),['REJECT','WIN']);q.close();q.join_thread();self.assertEqual(self.store.state('n').revision,2)
 def test_crash(self):
  old=self.add(observation());p=CTX.Process(target=crash,args=(self.path,));p.start();p.join(3);self.assertEqual(p.exitcode,72);self.store.close();self.store=WorldStore(self.path);self.assertEqual(old,self.store.state('n'))
