from parallel_test_helpers import *
import multiprocessing,os

def crash(path,point):
 r=ParallelRegistry(path);r.checkpoint=lambda p:os._exit(71) if point==p else None;w=setup()[1];r.change('n','work',0,'CLAIM',w.tasks[0].task_id)
def contend(path,barrier,q):
 r=ParallelRegistry(path);barrier.wait(timeout=5)
 try:r.change('n','work',0,'CLAIM',setup()[1].tasks[0].task_id);q.put('WIN')
 except ValueError:q.put('REJECT')
 finally:r.close()
class Recovery(Fixture,unittest.TestCase):
 def test_before_commit(self):self.check_crash('before_commit',0)
 def test_after_commit(self):self.check_crash('after_commit',1)
 def check_crash(self,point,revision):
  self.create();ctx=multiprocessing.get_context('fork');p=ctx.Process(target=crash,args=(self.path,point));p.start();p.join(5);self.assertFalse(p.is_alive());self.assertEqual(p.exitcode,71);self.assertEqual(self.r.read('n','work').revision,revision)
 def test_concurrent_claim(self):
  self.create();ctx=multiprocessing.get_context('fork');barrier=ctx.Barrier(2);q=ctx.Queue();ps=[ctx.Process(target=contend,args=(self.path,barrier,q)) for _ in range(2)]
  for p in ps:p.start()
  for p in ps:p.join(5);self.assertFalse(p.is_alive());self.assertEqual(p.exitcode,0)
  self.assertEqual(sorted([q.get(timeout=1),q.get(timeout=1)]),['REJECT','WIN']);q.close();q.join_thread();self.assertEqual(self.r.read('n','work').revision,1)
