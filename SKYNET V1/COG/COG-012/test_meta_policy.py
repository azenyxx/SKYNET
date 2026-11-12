from meta_test_helpers import *
from cognitive_meta_policy import decide
class PolicyTests(unittest.TestCase):
 def test_continue_advisory(self):d=decide(trace(),budget());self.assertEqual(d.action,'CONTINUE');self.assertFalse(d.executable or d.production_authorized or d.trusted_verification)
 def test_invalid_stop(self):self.assertEqual(decide(trace(change=('PLAN_RESULT','REJECTED')),budget()).action,'STOP')
 def test_latched(self):self.assertEqual(decide(trace(),budget(),stop_latched=True).action,'STOP')
 def test_exhaustion(self):self.assertEqual(decide(trace(),replace(budget(),limits=(6,10,10,1000,1000))).action,'STOP')
 def test_retry(self):self.assertEqual(decide(trace(),replace(budget(),retries_used=2)).action,'STOP')
 def test_reconsider(self):self.assertEqual(decide(trace(),replace(budget(),retries_used=1,retry_limit=2)).action,'RECONSIDER')
 def test_missing(self):self.assertEqual(decide(trace(change=('MEMORY','MISSING')),budget()).action,'REQUEST_EVIDENCE')
 def test_abstain(self):self.assertEqual(decide(trace(change=('CAUSAL','NOT_IDENTIFIABLE')),budget()).action,'ABSTAIN')

 def test_retry_limit_reached(self):self.assertEqual(decide(trace(),replace(budget(),retries_used=1)).action,'STOP')
