from meta_test_helpers import *
from cognitive_meta_tracing import validate_trace
class TraceTests(unittest.TestCase):
 def test_valid(self):self.assertEqual(validate_trace(trace()),())
 def test_missing(self):t=trace();self.assertEqual(validate_trace(replace(t,events=t.events[:-1])),('END',))
 def test_duplicate(self):
  t=trace()
  with self.assertRaises(MetaContractError):validate_trace(replace(t,events=t.events+(t.events[-1],)))
 def test_order(self):
  t=trace();es=list(t.events);es[0]=replace(es[0],kind='END')
  with self.assertRaises(MetaContractError):validate_trace(replace(t,events=tuple(es)))
 def test_namespace(self):
  t=trace()
  with self.assertRaises(MetaContractError):validate_trace(replace(t,events=(replace(t.events[0],namespace='other'),)+t.events[1:]))
 def test_bound(self):
  with self.assertRaises(MetaContractError):replace(trace(),events=trace().events*22)
 def test_resource_regression(self):
  t=trace()
  with self.assertRaises(MetaContractError):validate_trace(replace(t,events=t.events[:-1]+(replace(t.events[-1],usage=(0,0,0,0,0)),)))
