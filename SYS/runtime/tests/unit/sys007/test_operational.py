import unittest,json
from skynet_sys_recovery.operational import LeaseRecovery,RecoveryContractError
from skynet_sys_workers import WorkerError
from skynet_sys.canonical import FrozenJSON
from test_workers import fixture,worker
class LeaseTests(unittest.TestCase):
 def fixture(self):
  w=fixture();w.register('admin',worker(),0);w.lifecycle('admin','w','AVAILABLE',0);l=w.assign('admin','w','task','d','cognitive.reason',1,0,5,1);return LeaseRecovery(w),l
 def test_transition(self):
  r,l=self.fixture();status,e=r.release('admin','op',l.lease_id,0);self.assertEqual(status,'COMPLETED');self.assertNotEqual(e.pre_state_digest,e.post_state_digest);self.assertEqual(r.workers.leases[l.lease_id].lease_state,'REVOKED');print('POSTCONDITION '+json.dumps(dict(vars(e),audit_commitment=e.audit_commitment)))
 def test_unauthorized(self):
  r,l=self.fixture();before=r.workers.state_digest()
  with self.assertRaisesRegex(WorkerError,'^DENIED$'):r.release('w','op',l.lease_id,0)
  self.assertEqual(before,r.workers.state_digest());self.assertEqual(r.records,())
 def test_stale_completion(self):
  r,l=self.fixture();r.release('admin','op',l.lease_id,0);before=r.workers.state_digest()
  with self.assertRaisesRegex(WorkerError,'^LEASE_STATE$'):r.workers.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0)
  self.assertEqual(before,r.workers.state_digest())
 def test_idempotent(self):
  r,l=self.fixture();r.release('admin','op',l.lease_id,0);before=r.workers.state_digest();status,e=r.release('admin','op',l.lease_id,0);self.assertEqual(status,'IDEMPOTENT_NOOP');self.assertEqual(before,r.workers.state_digest());self.assertEqual(len(r.records),1)
 def test_terminal(self):
  r,l=self.fixture();r.workers.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0);before=r.workers.state_digest()
  with self.assertRaisesRegex(RecoveryContractError,'^LEASE_STATE$'):r.release('admin','op',l.lease_id,0)
  self.assertEqual(before,r.workers.state_digest())
 def test_capacity(self):
  r,l=self.fixture();r.capacity=1;r.release('admin','op',l.lease_id,0);l2=r.workers.assign('admin','w','task2','d','cognitive.reason',1,0,5,1);before=r.workers.state_digest()
  with self.assertRaisesRegex(RecoveryContractError,'^AUDIT_CAPACITY$'):r.release('admin','op2',l2.lease_id,0)
  self.assertEqual(before,r.workers.state_digest())
 def test_unknown(self):
  r,l=self.fixture()
  with self.assertRaisesRegex(RecoveryContractError,'^UNKNOWN_LEASE$'):r.release('admin','op','missing',0)
 def test_restore_blocked(self):
  r,l=self.fixture();before=r.workers.state_digest()
  with self.assertRaisesRegex(RecoveryContractError,'^BLOCKED_CONTRACT_NO_RESTORE_API$'):r.restore('admin','checkpoint')
  self.assertEqual(before,r.workers.state_digest())
