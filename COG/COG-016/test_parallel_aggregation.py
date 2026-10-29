from parallel_test_helpers import *
class Tests(Fixture,unittest.TestCase):
 def done(self):
  p,w=self.create();o,_=run(p,w,self.r);return w,o
 def test_reorder(self):
  w,o=self.done();self.assertEqual(aggregate(w,o.states[::-1]),o)
 def test_duplicate_exact(self):
  w,o=self.done();self.assertEqual(aggregate(w,o.states+(o.states[0],)),o)
 def test_conflict(self):
  w,o=self.done()
  with self.assertRaises(ValueError):aggregate(w,o.states+(replace(o.states[0],output='0'),))
 def test_missing(self):
  w,o=self.done()
  with self.assertRaises(ValueError):aggregate(w,o.states[:1])
 def test_commitment(self):
  w,o=self.done()
  with self.assertRaises(ValueError):aggregate(w,(replace(o.states[0],result_commitment='0'*64),o.states[1]))
 def test_unfinished(self):
  p,w=self.create()
  with self.assertRaises(ValueError):aggregate(w,self.r.read('n','work').states)
