from research_test_helpers import *
from cognitive_research_gaps import detect_gaps
from cognitive_research_hypotheses import generate
from cognitive_research_evaluation import evaluate
class EvaluationTests(unittest.TestCase):
 def test_negative(self):d=domain('A');q,h=generate(d,detect_gaps(d)[0]);self.assertIn('REFUTED_WITHIN_MODEL',{r.status for r in evaluate(d,h,d.observations)})
 def test_fabrication(self):
  d=domain('A');q,h=generate(d,detect_gaps(d)[0])
  with self.assertRaises(ResearchError):evaluate(d,h,(replace(d.observations[0],y=99),))
