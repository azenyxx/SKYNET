from research_test_helpers import *
import multiprocessing,os
CTX=multiprocessing.get_context('fork')
def writer(path,s,bar,q,crash):
 r=Registry(path)
 try:
  if bar:bar.wait(2)
  if crash:Registry.checkpoint=staticmethod(lambda p:os._exit(75) if p==crash else None)
  r.append(s,0)
  if q:q.put('WIN')
 except ResearchError:
  if q:q.put('REJECT')
 finally:r.close()
class RecoveryTests(Fixture,unittest.TestCase):
 def empty_target(self):
  s=self.run_cycle();p=str(Path(self.tmp.name)/'target');r=Registry(p,True);r.close();return s,p
 def test_concurrent(self):
  s,path=self.empty_target();bar=CTX.Barrier(2);q=CTX.Queue();ps=[CTX.Process(target=writer,args=(path,s,bar,q,None)) for _ in range(2)]
  for p in ps:p.start()
  for p in ps:p.join(3);self.assertEqual(p.exitcode,0)
  self.assertEqual(sorted(q.get(timeout=1) for _ in ps),['REJECT','WIN']);q.close();q.join_thread();r=Registry(path);self.assertEqual(len(r.verify()),1);r.close()
 def crash(self,point,count):
  s,path=self.empty_target();p=CTX.Process(target=writer,args=(path,s,None,None,point));p.start();p.join(3);self.assertEqual(p.exitcode,75);r=Registry(path);self.assertEqual(len(r.verify()),count);r.close()
 def test_before(self):self.crash('before_commit',0)
 def test_after(self):self.crash('after_commit',1)
