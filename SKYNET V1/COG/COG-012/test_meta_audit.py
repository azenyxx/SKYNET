from meta_test_helpers import *
class AuditTests(Fixture,unittest.TestCase):
 def test_restart(self):a=self.a.append(trace(),budget(),0);self.a.close();self.a=MetaAudit(self.path);self.assertEqual(self.a.replay('n'),(a,))
 def test_duplicate(self):
  self.a.append(trace(),budget(),0)
  with self.assertRaises(MetaContractError):self.a.append(trace(),budget(),1)
 def test_namespace(self):self.a.append(trace(),budget(),0);self.assertEqual(self.a.replay('other'),())
 def test_stop_persistent(self):
  self.a.append(trace(change=('PLAN_RESULT','REJECTED')),budget(),0);self.a.close();self.a=MetaAudit(self.path);r=self.a.append(trace('next'),budget('next'),1);self.assertEqual(r.decision.action,'STOP')
 def test_incomplete_restart(self):
  t=trace();a=self.a.append(replace(t,events=t.events[:-1]),budget(),0);self.assertEqual(a.decision.action,'ABSTAIN');self.a.close();self.a=MetaAudit(self.path);self.assertEqual(self.a.replay('n')[0],a)
