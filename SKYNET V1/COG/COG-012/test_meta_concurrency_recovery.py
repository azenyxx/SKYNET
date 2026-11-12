from meta_test_helpers import *
import multiprocessing,os
CTX=multiprocessing.get_context('fork')
def writer(path,tid,bar,q,crash=None):
 a=MetaAudit(path)
 try:
  if bar:bar.wait(2)
  if crash:MetaAudit.checkpoint=staticmethod(lambda p:os._exit(74) if p==crash else None)
  a.append(trace(tid),budget(tid),0)
  if q:q.put('WIN')
 except MetaContractError:
  if q:q.put('REJECT')
 finally:a.close()
class RecoveryTests(Fixture,unittest.TestCase):
 def test_two_processes(self):
  bar=CTX.Barrier(2);q=CTX.Queue();ps=[CTX.Process(target=writer,args=(self.path,'t'+str(i),bar,q)) for i in range(2)]
  for p in ps:p.start()
  for p in ps:p.join(3);self.assertEqual(p.exitcode,0)
  self.assertEqual(sorted(q.get(timeout=1) for _ in ps),['REJECT','WIN']);q.close();q.join_thread();self.assertEqual(len(self.a.verify()),1)
 def crash(self,point,count):
  p=CTX.Process(target=writer,args=(self.path,'trace',None,None,point));p.start();p.join(3);self.assertEqual(p.exitcode,74);self.a.close();self.a=MetaAudit(self.path);self.assertEqual(len(self.a.verify()),count)
 def test_before_commit(self):self.crash('before_commit',0)
 def test_after_commit(self):self.crash('after_commit',1)
