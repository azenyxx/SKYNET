from research_test_helpers import *
class StrategyTests(Fixture,unittest.TestCase):
 def test_bounded_cycle(self):s=self.run_cycle();self.assertEqual(s.iterations,1);self.assertEqual(s.terminal,'STOP');self.assertEqual(len(s.experiments),1);self.assertEqual(sum(r.status=='REFUTED_WITHIN_MODEL' for r in s.results),2)
 def test_no_budget(self):s=self.run_cycle(b=budget(experiments=0));self.assertEqual(s.iterations,0);self.assertEqual(s.decisions[-1].reason,'BUDGET')
 def test_confounding(self):s=self.run_cycle('B');self.assertEqual(s.terminal,'REQUEST_EVIDENCE');self.assertTrue(all(r.status=='NOT_IDENTIFIABLE' for r in s.results))
 def test_contradiction(self):s=self.run_cycle('C');self.assertEqual(s.terminal,'ABSTAIN');self.assertEqual(len(s.observations),2);self.assertTrue(all(r.status=='INCONCLUSIVE' for r in s.results))
