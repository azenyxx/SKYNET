from parallel_test_helpers import *
class Tests(Fixture,unittest.TestCase):
 def test_reopen(self):
  p,w=self.create();run(p,w,self.r);before=self.r.read('n','work');self.r.close();self.r=ParallelRegistry(self.path);self.assertEqual(self.r.read('n','work'),before)
 def test_duplicate_create(self):
  p,w=self.create()
  with self.assertRaises(ValueError):self.r.change('n','work',0,'CREATE',workload=w)
 def test_stale(self):
  p,w=self.create();self.r.change('n','work',0,'CLAIM',w.tasks[0].task_id)
  with self.assertRaises(ValueError):self.r.change('n','work',0,'CLAIM',w.tasks[1].task_id)
 def test_not_ready(self):
  p,w=self.create(dependent=True)
  with self.assertRaises(ValueError):self.r.change('n','work',0,'CLAIM',w.tasks[1].task_id)
 def test_late(self):
  p,w=self.create();s=self.r.change('n','work',0,'CLAIM',w.tasks[0].task_id);self.r.change('n','work',s.revision,'STOP')
  with self.assertRaises(ValueError):self.r.change('n','work',2,'RESULT',w.tasks[0].task_id,WorkerResultV1(w.tasks[0].commitment,1,'29'),'SUCCEEDED')
 def test_namespace(self):
  self.create()
  with self.assertRaises(ValueError):self.r.read('other','work')
 def test_corruption(self):
  self.create();self.r.db.execute('DROP TRIGGER no_update')
  with self.assertRaises(ValueError):self.r.verify()
 def test_head_tamper(self):
  self.create();self.r.db.execute('DELETE FROM heads')
  with self.assertRaises(ValueError):self.r.verify()
 def test_recover_ambiguous(self):
  p,w=self.create();self.r.change('n','work',0,'CLAIM',w.tasks[0].task_id);out,stats=run(p,w,self.r);self.assertEqual(stats['go'],0);self.assertEqual(out.states[0].status,'UNKNOWN')
