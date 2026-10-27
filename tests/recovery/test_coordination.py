import unittest
from dataclasses import replace
from skynet.system import System
from skynet.coordination import RecoveryRequest,CoordinationError
from skynet_sys.canonical import FrozenJSON
class CoordinationTests(unittest.TestCase):
 def fixture(self,action):
  h=System(1,1);h.run('admit');h.run('dispatch',1)
  if action=='RETRY':h.run('recover','REQUEUE','t0','failed')
  l=h.workers.leases[h.leases['t0']];r=h.rows()['t0'];q=RecoveryRequest('op','t0',l.attempt,r[9],l.worker_id,l.lease_id,'admin',r[11],l.lease_state,action);return h,q
 def scenario(self,action,case):
  h,q=self.fixture(action);c=h.coordinator;before=h.state_digest()
  if case=='authorized':
   e=h.recovery.execute(action,q);self.assertEqual(e.status,'SUCCESS');self.assertEqual(e.postcondition_result,'PASS');self.assertNotEqual(before,h.state_digest());self.assertIs(c.scheduler,h.scheduler);self.assertIs(c.workers,h.workers)
  elif case=='unauthorized':
   with self.assertRaisesRegex(CoordinationError,'^AUTHORIZATION$'):c.execute(replace(q,authorized_actor='evil'),0)
   self.assertEqual(before,h.state_digest())
  elif case=='invalid_state':
   e=c.execute(replace(q,expected_scheduler_state='SUCCEEDED'),0);self.assertEqual((e.status,e.reason),('REJECTED','STATE_CONFLICT'));self.assertEqual(e.scheduler_pre_state,e.scheduler_post_state);self.assertEqual(e.worker_pre_state,e.worker_post_state)
  elif case=='duplicate':
   first=c.execute(q,0);state=h.state_digest();self.assertEqual(c.execute(q,0),first);self.assertEqual(state,h.state_digest());self.assertEqual(len([e for e in c.records if e.operation_id=='op']),1)
  elif case=='postconditions':
   e=c.execute(q,0);self.assertEqual(e.status,'SUCCESS');row=h.rows()['t0'];self.assertEqual(h.workers.leases[q.lease_id].lease_state,'REVOKED');self.assertEqual(row[11],{'RETRY':'RUNNING','REQUEUE':'READY','RELEASE_LEASE':'CANCELLED'}[action]);self.assertEqual(sum(l.lease_state=='ACTIVE' for l in h.workers.leases.values()),int(action=='RETRY'))
   if action=='RETRY':self.assertNotEqual(row[9],q.assignment_id);self.assertEqual(row[7],2);self.assertEqual(h.workers.leases[e.new_lease_id].attempt,2)
  elif case=='stale_identity':
   e=c.execute(replace(q,assignment_id='stale'),0);self.assertEqual((e.status,e.reason),('REJECTED','STALE_ASSIGNMENT'));self.assertEqual(e.scheduler_pre_state,e.scheduler_post_state);self.assertEqual(e.worker_pre_state,e.worker_post_state)
  elif case=='stale_completion':
   self.assertEqual(c.execute(q,0).status,'SUCCESS');state=h.state_digest()
   with self.assertRaisesRegex(ValueError,'^LEASE_STATE$'):h.workers.complete(q.worker_id,q.lease_id,q.attempt_id,'d0',FrozenJSON.make({}),0)
   self.assertEqual(state,h.state_digest())
  elif case=='conflicting_duplicate':
   c.execute(q,0);state=h.state_digest()
   with self.assertRaisesRegex(CoordinationError,'^CONFLICTING_DUPLICATE$'):c.execute(replace(q,assignment_id='changed'),0)
   self.assertEqual(state,h.state_digest())
  else:raise AssertionError(case)
for action in ('RETRY','REQUEUE','RELEASE_LEASE'):
 for case in ('authorized','unauthorized','invalid_state','duplicate','postconditions','stale_identity','stale_completion','conflicting_duplicate'):
  def test(self,a=action,c=case):self.scenario(a,c)
  setattr(CoordinationTests,'test_'+action+'_'+case,test)
class BoundaryTests(CoordinationTests):
 # Explicitly prevent inherited generated tests from being counted twice below.
 def test_audit_capacity(self):
  h,q=self.fixture('REQUEUE');h.coordinator.capacity=1;h.coordinator.execute(replace(q,assignment_id='bad'),0);before=h.state_digest()
  with self.assertRaisesRegex(CoordinationError,'^AUDIT_CAPACITY$'):h.coordinator.execute(replace(q,operation_id='fresh'),0)
  self.assertEqual(before,h.state_digest())
 def test_partial_transition(self):
  h,q=self.fixture('REQUEUE');h.scheduler.policy=replace(h.scheduler.policy,max_operations=len(h.scheduler._journal));e=h.coordinator.execute(q,0);self.assertEqual((e.status,e.reason),('PARTIAL_TRANSITION','OPERATION_BUDGET'));self.assertEqual(h.rows()['t0'][11],'RUNNING');self.assertEqual(h.workers.leases[q.lease_id].lease_state,'REVOKED')
  with self.assertRaisesRegex(CoordinationError,'^PARTIAL_TRANSITION_BLOCKED$'):h.coordinator.execute(replace(q,operation_id='next'),0)
 def test_budget_exhaustion(self):
  h=System(1,1,1);h.run('admit');h.run('dispatch',1);h.run('recover','REQUEUE','t0','failure');l=h.workers.leases[h.leases['t0']];row=h.rows()['t0'];q=RecoveryRequest('retry','t0',1,row[9],'w0',l.lease_id,'admin','FAILED','REVOKED','RETRY');e=h.coordinator.execute(q,0);self.assertEqual((e.status,e.reason),('REJECTED','RETRY_STATE'));self.assertEqual(len(h.workers.leases),1);self.assertEqual(row[7],row[6])
 def test_terminal_no_resurrection(self):
  h,q=self.fixture('RELEASE_LEASE');h.coordinator.execute(q,0);e=h.coordinator.execute(replace(q,operation_id='new',recovery_policy='RETRY',expected_scheduler_state='CANCELLED',expected_worker_state='REVOKED'),0);self.assertEqual((e.status,e.reason),('REJECTED','RETRY_STATE'))
 def test_audit_tamper(self):
  h,q=self.fixture('REQUEUE');e=h.coordinator.execute(q,0)
  with self.assertRaisesRegex(CoordinationError,'^AUDIT_TAMPER$'):h.coordinator.verify_audit((replace(e,status='FALSE'),),e.audit_commitment)
 def test_scheduler_replay_new_operations(self):
  h,q=self.fixture('REQUEUE');h.run('recover','REQUEUE','t0','failure');h.run('recover','RETRY','t0','retry');s=h.scheduler.replay('admin',tuple(h.scheduler._journal));self.assertEqual(s.checkpoint('admin'),h.scheduler.checkpoint('admin'))
 def test_unified_tamper(self):
  h,q=self.fixture('REQUEUE');records=h.records[:-1]+(h.records[-1][:-1]+('f'*64,),)
  with self.assertRaisesRegex(CoordinationError,'^JOURNAL_TAMPERED$'):h.replay(records,h.head)
 def test_replay_no_source_side_effect(self):
  h,q=self.fixture('REQUEUE');h.run('recover','REQUEUE','t0','failure');h.run('recover','RETRY','t0','retry');before=h.state_digest();other=h.replay();self.assertEqual(before,h.state_digest());self.assertEqual(before,other.state_digest());self.assertIsNot(h.workers,other.workers)
# Move boundary methods to a fresh class without duplicating inherited tests.
BoundaryTests=type('BoundaryTests',(unittest.TestCase,),{k:v for k,v in BoundaryTests.__dict__.items() if k.startswith('test_')}|{'fixture':CoordinationTests.fixture})

class MoreBoundaryTests(unittest.TestCase):
 fixture=CoordinationTests.fixture
 def test_scheduler_recovery_default_deny(self):
  h,q=self.fixture('REQUEUE');h.scheduler.policy=replace(h.scheduler.policy,grants=tuple(g for g in h.scheduler.policy.grants if g!=('admin','recover')));before=h.workers.state_digest()
  with self.assertRaisesRegex(CoordinationError,'^AUTHORIZATION$'):h.coordinator.execute(q,0)
  self.assertEqual(before,h.workers.state_digest())
 def test_request_bool_attempt(self):
  h,q=self.fixture('REQUEUE')
  with self.assertRaisesRegex(CoordinationError,'^ATTEMPT$'):replace(q,attempt_id=True)
 def test_request_policy(self):
  h,q=self.fixture('REQUEUE')
  with self.assertRaisesRegex(CoordinationError,'^POLICY$'):replace(q,recovery_policy='DEPLOY')
 def test_scheduler_unauthorized_direct_recovery(self):
  h,q=self.fixture('REQUEUE');before=h.scheduler.checkpoint('admin')
  with self.assertRaisesRegex(ValueError,'^AUTHORIZATION$'):h.scheduler.recover_assignment('evil',q.task_id,q.assignment_id,q.attempt_id,'REQUEUE',0)
  self.assertEqual(before,h.scheduler.checkpoint('admin'))
 def test_worker_retry_budget_partial(self):
  h,q=self.fixture('RETRY');h.workers.workers['w0']=replace(h.workers.workers['w0'],resource_limits=replace(h.workers.workers['w0'].resource_limits,attempts=1));e=h.coordinator.execute(q,0);self.assertEqual((e.status,e.reason),('PARTIAL_TRANSITION','ATTEMPT'));self.assertTrue(h.coordinator.blocked);self.assertEqual(len(h.workers.leases),1)
 def test_worker_owner_binding(self):
  h,q=self.fixture('REQUEUE');e=h.coordinator.execute(replace(q,worker_id='w9'),0);self.assertEqual((e.status,e.reason),('REJECTED','LEASE_BINDING'))
