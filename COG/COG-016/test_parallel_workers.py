from parallel_test_helpers import *
class Tests(Fixture,unittest.TestCase):
 def test_parallel(self):
  p,w=self.create();out,stats=run(p,w,self.r);self.assertEqual(out.status,'COMPLETE_ISOLATED');self.assertEqual(stats['go'],2);self.assertEqual(stats['peak_active'],2);self.assertEqual(stats['reaped'],2)
 def test_dependency(self):
  p,w=self.create(dependent=True);o,s=run(p,w,self.r);self.assertEqual(o.status,'COMPLETE_ISOLATED');self.assertEqual(s['peak_active'],1)
 def test_crash(self):
  p,w=self.create();o,s=run(p,w,self.r,((w.tasks[0].task_id,'CRASH'),));self.assertEqual(o.status,'PARTIAL_FAILURE');self.assertEqual(s['reaped'],2)
 def test_timeout(self):
  p,w=self.create(timeout=30);o,s=run(p,w,self.r,((w.tasks[0].task_id,'DELAY'),));self.assertIn('TIMED_OUT',{x.status for x in o.states});self.assertEqual(s['cleanup_failures'],0)
 def test_stop(self):
  p,w=self.create();o,s=run(p,w,self.r,stop_after_go=True);self.assertTrue(self.r.read('n','work').stopped);self.assertEqual(s['go'],1);self.assertFalse(o.production_authorized)
 def test_replay(self):
  p,w=self.create();run(p,w,self.r)
  with self.assertRaises(ValueError):run(p,w,self.r)
 def test_wrong_plan(self):
  p,w=self.create()
  with self.assertRaises(ValueError):run(p,replace(w,plan_id='0'*64),self.r)
 def test_fault_allowlist(self):
  p,w=self.create()
  with self.assertRaises(ValueError):run(p,w,self.r,((w.tasks[0].task_id,'SHELL'),))
