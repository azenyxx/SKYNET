from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_resource(self):
  e=session().evaluation;self.assertEqual(e.candidate_metrics.correct,e.baseline_metrics.correct);self.assertLess(e.candidate_metrics.operations,e.baseline_metrics.operations)
 def test_accuracy(self):self.assertGreater(session('ACCURACY').evaluation.regressions,0)
 def test_research(self):
  e=session('RESEARCH').evaluation;self.assertLess(e.candidate_metrics.operations,e.baseline_metrics.operations)
 def test_transfer(self):
  e=session('TRANSFER').evaluation;self.assertGreater(e.candidate_metrics.correct,e.baseline_metrics.correct)
 def test_repeat(self):self.assertEqual(session(),session())
