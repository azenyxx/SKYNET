from world_test_helpers import *
from cognitive_causal_engine import reason,causal_claim
class CausalTests(unittest.TestCase):
 def test_chain(self):r=reason(model(),'0'*64);self.assertEqual(r.assignments,('x=0','y=0'));self.assertEqual(r.status,'HYPOTHETICAL')
 def test_confounding(self):self.assertEqual(reason(replace(model(),confounders=('u',)),'0'*64).status,'NOT_IDENTIFIABLE')
 def test_no_assumptions(self):self.assertEqual(reason(replace(model(),assumptions=()),'0'*64).status,'NOT_IDENTIFIABLE')
 def test_cycle(self):
  m=model();x=replace(m.equations[0],operator='COPY',parents=('y',));m=replace(m,equations=(x,m.equations[1]))
  with self.assertRaises(WorldError):reason(m,'0'*64)
 def test_correlation(self):self.assertEqual(causal_claim(WorldCausalEdgeV1('n',P,'HYPOTHESIZED','UNVERIFIED','x','y','CORRELATION',())),'NOT_IDENTIFIABLE')
