from research_test_helpers import *
from cognitive_research_gaps import detect_gaps
from cognitive_research_hypotheses import generate
class HypothesisTests(unittest.TestCase):
 def test_competing(self):d=domain('A');q,h=generate(d,detect_gaps(d)[0]);self.assertEqual(len({v.hypothesis_id for v in h}),3);self.assertEqual(generate(d,detect_gaps(d)[0]),(q,h))
 def test_injection(self):
  d=domain('A');q,h=generate(d,detect_gaps(d)[0])
  with self.assertRaises(ResearchError):replace(h[0],rule='EXECUTE_SHELL')
