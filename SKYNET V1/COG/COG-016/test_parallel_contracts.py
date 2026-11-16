from parallel_test_helpers import *
class Tests(unittest.TestCase):
 def test_canonical(self):
  p,w=setup();self.assertEqual(parse(WorkloadV1,canonical(w)),w)
 def test_workers(self):
  for n in (0,9):
   with self.assertRaises(ValueError):setup(workers=n)
 def test_timeout(self):
  with self.assertRaises(ValueError):setup(timeout=0)
 def test_queue(self):
  with self.assertRaises(ValueError):replace(setup()[1],queue_capacity=1)
 def test_digest(self):
  with self.assertRaises(ValueError):replace(setup()[1].tasks[0],input_digest='0'*64)
 def test_operation(self):
  with self.assertRaises(ValueError):replace(setup()[1].tasks[0],operation='SHELL')
 def test_duplicate(self):
  w=setup()[1]
  with self.assertRaises(ValueError):replace(w,tasks=(w.tasks[0],w.tasks[0]))
 def test_budget(self):
  with self.assertRaises(ValueError):replace(setup()[1],max_dispatches=0)
 def test_unknown(self):
  import json
  obj=json.loads(canonical(setup()[1]));obj['authority']=True
  with self.assertRaises(ValueError):parse(WorkloadV1,canonical(obj))
 def test_oversize(self):
  t=setup()[1].tasks[0]
  with self.assertRaises(ValueError):replace(t,payload='x'*4097)
