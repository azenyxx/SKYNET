from parallel_test_helpers import *
class Tests(unittest.TestCase):
 def test_real_hash(self):
  import hashlib
  p,w=setup();t=w.tasks[0];t=replace(t,operation='SHA256_TEXT_V1',payload='abc',input_digest=digest('Input',dict(operation='SHA256_TEXT_V1',payload='abc')));r=WorkerResultV1(t.commitment,1,execute(t));self.assertEqual(verify(t,r).output,hashlib.sha256(b'abc').hexdigest())
 def test_wrong_output(self):
  t=setup()[1].tasks[0]
  with self.assertRaises(ValueError):verify(t,WorkerResultV1(t.commitment,1,'0'))
 def test_binding(self):
  t=setup()[1].tasks[0]
  with self.assertRaises(ValueError):verify(t,WorkerResultV1('0'*64,1,'29'))
 def test_attempt(self):
  with self.assertRaises(ValueError):WorkerResultV1('0'*64,2,'29')
 def test_fabricated(self):
  with self.assertRaises(ValueError):verify(setup()[1].tasks[0],True)
 def test_numeric_bound(self):
  from cognitive_parallel_operators import inputs
  t=setup()[1].tasks[0];payload='10001';t=replace(t,payload=payload,input_digest=digest('Input',dict(operation=t.operation,payload=payload)))
  with self.assertRaises(ValueError):inputs(t)
