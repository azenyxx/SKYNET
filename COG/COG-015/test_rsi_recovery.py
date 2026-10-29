from rsi_test_helpers import *
import multiprocessing,os
# Child processes are isolated test fixtures, not executors or detached jobs.
def crash(path,point):
 r=ImprovementRegistry(path);r.checkpoint=lambda p:os._exit(71) if p==point else None;r.append(session(),0)
def race(path,barrier,q):
 r=ImprovementRegistry(path);barrier.wait(timeout=5)
 try:r.append(session(),0);q.put('WIN')
 except RSIError:q.put('REJECT')
 finally:r.close()
class Recovery(unittest.TestCase):
 def test_crashes(self):
  ctx=multiprocessing.get_context('fork')
  for point,expected in (('before_commit',0),('after_commit',1)):
   with tempfile.TemporaryDirectory() as d:
    path=str(Path(d)/'r');r=ImprovementRegistry(path,True);r.close();p=ctx.Process(target=crash,args=(path,point));p.start();p.join(5);self.assertFalse(p.is_alive());self.assertEqual(p.exitcode,71);r=ImprovementRegistry(path);self.assertEqual(len(r.verify()),expected);r.close()
 def test_race(self):
  ctx=multiprocessing.get_context('fork')
  with tempfile.TemporaryDirectory() as d:
   path=str(Path(d)/'r');r=ImprovementRegistry(path,True);r.close();q=ctx.Queue();barrier=ctx.Barrier(2);ps=[ctx.Process(target=race,args=(path,barrier,q)) for _ in range(2)]
   for p in ps:p.start()
   for p in ps:p.join(5);self.assertFalse(p.is_alive());self.assertEqual(p.exitcode,0)
   self.assertEqual(sorted([q.get(timeout=1),q.get(timeout=1)]),['REJECT','WIN']);q.close();q.join_thread();r=ImprovementRegistry(path);self.assertEqual(len(r.verify()),1);r.close()
