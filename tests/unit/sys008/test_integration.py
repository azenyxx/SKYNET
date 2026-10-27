import unittest
from dataclasses import replace,FrozenInstanceError
from skynet_sys_integration import Harness,IntegrationError
class Scenarios(unittest.TestCase):pass
for n in range(1,13):
 def test(self,n=n):
  h=Harness();r=h.run(n);self.assertEqual(r.status,'PASS');self.assertEqual(r.actual_outcome,r.expected_outcome);self.assertEqual(h.state_digest(),h.replay(h.journal));self.assertTrue(r.audit_references)
 setattr(Scenarios,'test_E2E_'+str(n).zfill(2),test)
class Boundaries(unittest.TestCase):
 def test_bool_capacity(self):
  with self.assertRaisesRegex(IntegrationError,'^CAPACITY$'):Harness(True)
 def test_zero_capacity(self):
  with self.assertRaisesRegex(IntegrationError,'^CAPACITY$'):Harness(0)
 def test_oversize_capacity(self):
  with self.assertRaisesRegex(IntegrationError,'^CAPACITY$'):Harness(129)
 def test_bad_scenario(self):
  with self.assertRaisesRegex(IntegrationError,'^SCENARIO$'):Harness().run(13)
 def test_duplicate(self):
  h=Harness();h.run(10);before=h.state_digest()
  with self.assertRaisesRegex(IntegrationError,'^DUPLICATE_SCENARIO$'):h.run(10)
  self.assertEqual(before,h.state_digest())
 def test_saturation(self):
  h=Harness(1);h.run(10);before=h.state_digest()
  with self.assertRaisesRegex(IntegrationError,'^AUDIT_CAPACITY$'):h.run(4)
  self.assertEqual(before,h.state_digest())
 def test_tamper(self):
  h=Harness();h.run(10)
  with self.assertRaisesRegex(IntegrationError,'^TAMPER$'):h.replay((replace(h.journal[0],output_commitment='f'*64),))
 def test_truncation(self):
  h=Harness();h.run(10)
  with self.assertRaisesRegex(IntegrationError,'^REPLAY_LENGTH$'):h.replay(())
 def test_sequence(self):
  h=Harness();h.run(10)
  with self.assertRaisesRegex(IntegrationError,'^CHAIN$'):h.replay((replace(h.journal[0],sequence=9),))
 def test_immutable(self):
  r=Harness().run(10)
  with self.assertRaises(FrozenInstanceError):r.status='ACCEPTED'
 def test_determinism(self):
  a=Harness();b=Harness();self.assertEqual(a.run(10),b.run(10))
 def test_replay_readonly(self):
  h=Harness();h.run(10);before=(h.journal,h.results,h.state_digest());h.replay(h.journal);self.assertEqual(before,(h.journal,h.results,h.state_digest()))

class Safety(unittest.TestCase):
 def test_revoked(self):
  from skynet_sys_integration.harness import integrated,FrozenJSON,reject
  w=integrated();l=w.dispatch('task','d',1,0);w.revoke(l.lease_id,0);before=w.state_digest();reject('LEASE_STATE',lambda:w.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0));self.assertEqual(before,w.state_digest())
 def test_cancelled(self):
  from skynet_sys_integration.harness import integrated,FrozenJSON,reject
  w=integrated();l=w.dispatch('task','d',1,0);w.cancel(l.lease_id,0);before=w.state_digest();reject('LEASE_STATE',lambda:w.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0));self.assertEqual(before,w.state_digest())
 def test_terminal_and_evidence(self):
  from skynet_sys_integration.harness import IntegrationTests,payload,assessment,reject
  i,q,l=IntegrationTests().fixture();i.run('open',(q,payload()),l.lease_id);a=assessment(q);i.run('submit',(a,0));d=i.run('evaluate',('r',0));before=i.state_digest();reject('TERMINAL',lambda:i.run('submit',(a,0)));self.assertEqual(before,i.state_digest());self.assertEqual(a.evidence_refs[0].verification_status,'UNVERIFIED');self.assertEqual(i.engine.rounds['r']['decision'],d)
 def test_workload(self):
  import json
  from skynet_sys_integration.harness import workload
  r=workload();self.assertEqual(r['tasks_completed'],20);self.assertEqual(r['workers'],10);self.assertGreaterEqual(r['participating_verifiers'],3);self.assertEqual(r['state_digest'],r['replay_digest']);print('WORKLOAD '+json.dumps(r))
