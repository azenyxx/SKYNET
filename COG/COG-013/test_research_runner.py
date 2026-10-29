from research_test_helpers import *
from cognitive_research_gaps import detect_gaps
from cognitive_research_hypotheses import generate
from cognitive_research_design import design
from cognitive_research_runner import run_experiment
class RunnerTests(unittest.TestCase):
 def spec(self):d=domain('A');q,h=generate(d,detect_gaps(d)[0]);return d,design(d,q,h,d.observations)
 def test_positive(self):d,e=self.spec();o,p=run_experiment(d,e,budget());self.assertEqual((o.x,o.y),(2,5));self.assertEqual(p.observation_commitment,o.commitment)
 def test_deterministic(self):d,e=self.spec();self.assertEqual(run_experiment(d,e,budget()),run_experiment(d,e,budget()))
 def test_budget(self):
  d,e=self.spec()
  with self.assertRaises(ResearchError):run_experiment(d,e,budget(experiments=0))
 def test_unknown_operation(self):
  d,e=self.spec()
  with self.assertRaises(ResearchError):replace(e,operation='HTTP')
 def test_scope(self):
  d,e=self.spec()
  with self.assertRaises(ResearchError):run_experiment(d,replace(e,namespace='other'),budget())
