import unittest
from unittest.mock import patch
from skynet.system import System
from skynet_sys_workers import Orchestrator
from skynet_sys_transport.bus import Bus
class QualificationTests(unittest.TestCase):
 def ready(self):
  h=System(1,1);h.run('admit');h.run('dispatch',1);return h
 def test_replay_no_worker_execution_or_transport_publication(self):
  h=self.ready();h.run('complete','t0');before=h.state_digest()
  with patch.object(Orchestrator,'complete',side_effect=AssertionError('REPLAY_WORKER_EXECUTION')),patch.object(Bus,'publish',side_effect=AssertionError('REPLAY_TRANSPORT_PUBLICATION')):
   a=h.replay();b=h.replay()
  self.assertEqual(a.state_digest(),before);self.assertEqual(b.state_digest(),before);self.assertEqual(h.state_digest(),before)
 def test_malformed_command_cannot_mutate_before_audit(self):
  h=self.ready();before=h.state_digest();count=len(h.records)
  with self.assertRaises(ValueError):h.run('complete','t0',object())
  self.assertEqual(before,h.state_digest());self.assertEqual(count,len(h.records));self.assertEqual(h.workers.leases[h.leases['t0']].lease_state,'ACTIVE')
 def restore_fixture(self):
  h=System(1,1);h.run('control',1,0);h.run('checkpoint','cp');h.run('control',2,1);return h
 def test_restore_host_idempotency(self):
  h=self.restore_fixture();first=h.run('restore','cp','r');before=h.memory.digest();second=h.run('restore','cp','r');self.assertEqual(first.status,'RESTORED');self.assertEqual(second.status,'IDEMPOTENT_NOOP');self.assertEqual(h.memory.digest(),before)
 def test_actual_active_worker_failure_retry(self):
  h=self.ready();old=h.leases['t0'];h.run('fail_worker','w0');self.assertEqual(h.rows()['t0'][11],'READY');self.assertEqual(h.workers.leases[old].lease_state,'REVOKED');h.run('activate','w0');e=h.run('recover','RETRY','t0','retry');self.assertEqual(e.status,'SUCCESS');self.assertNotEqual(e.new_lease_id,old);self.assertEqual(h.rows()['t0'][7],2)
 def test_memory_provenance_binding(self):
  from dataclasses import replace
  from skynet_sys_memory import Operation
  h=self.ready();h.run('complete','t0');record=h.memory.read('admin','agent','result:t0');h.memory.transact('admin','forge',(Operation('agent','result:t0','UPDATE',record.version,record.payload,(replace(record.evidence_refs[0],producer_id='other'),)),),0)
  before=h.engine.state_digest()
  with self.assertRaisesRegex(ValueError,'RESULT_BINDING'):h.run('verify','t0','single')
  self.assertEqual(before,h.engine.state_digest())
 def test_replay_twice_readonly_snapshot(self):
  from dataclasses import FrozenInstanceError
  h=self.ready();h.run('complete','t0');a=h.replay();b=h.replay();self.assertEqual(a.state_digest(),b.state_digest());self.assertEqual(a.boundary,'TRUSTED_FINAL_SNAPSHOT_AUDIT_V1')
  with self.assertRaises(FrozenInstanceError):a.head='changed'
 def test_replay_rejects_unjournaled_state(self):
  h=self.ready();h.run('complete','t0');h.workers.fail_worker('admin','w0',0)
  with self.assertRaisesRegex(ValueError,'^SNAPSHOT_BINDING$'):h.replay()
 def test_replay_rejects_missing_history(self):
  h=self.ready();old=h.records;head=h.head;h.run('complete','t0')
  with self.assertRaisesRegex(ValueError,'^UNSUPPORTED_HISTORY$'):h.replay(old,head)
 def test_restore_changed_checkpoint_id_conflicts(self):
  h=self.restore_fixture();h.run('restore','cp','r');before=h.memory.digest()
  with self.assertRaisesRegex(ValueError,'CONFLICTING_RESTORE'):h.run('restore','another','r')
  self.assertEqual(before,h.memory.digest())
 def test_safe001_actual_unauthorized_admission(self):
  from skynet_sys.tasks import TaskRequest
  from skynet_sys.canonical import FrozenJSON
  from skynet.system import T
  h=System(1,1);before=h.scheduler.checkpoint('admin');q=TaskRequest('evil',None,'trace','evil','cognitive.reason',FrozenJSON.make({}),0,'2026-10-25T00:01:00.000000Z','evil',T)
  with self.assertRaisesRegex(ValueError,'^AUTHORIZATION$'):h.scheduler.admit('evil',((q,(),1),),0)
  self.assertEqual(before,h.scheduler.checkpoint('admin'))
 def test_safe005_duplicate_active_assignment(self):
  h=self.ready();before=h.workers.state_digest()
  with self.assertRaisesRegex(ValueError,'^TASK_ACTIVE$'):h.workers.assign('admin','w0','t0','d0','cognitive.reason',2,0,5,1)
  self.assertEqual(before,h.workers.state_digest())
 def test_safe015_result_binding(self):
  from skynet_sys_memory import Operation
  from skynet_sys.canonical import FrozenJSON
  h=self.ready();h.run('complete','t0');r=h.memory.read('admin','agent','result:t0');h.memory.transact('admin','bad-result',(Operation('agent','result:t0','UPDATE',r.version,FrozenJSON.make({'other':'result'}),r.evidence_refs),),0);before=h.engine.state_digest()
  with self.assertRaisesRegex(ValueError,'RESULT_BINDING'):h.run('verify','t0','single')
  self.assertEqual(before,h.engine.state_digest())
 def test_host_arity_preflight(self):
  h=self.ready();before=h.state_digest()
  with self.assertRaisesRegex(ValueError,'^COMMAND_ARITY$'):h.run('complete','t0','extra')
  self.assertEqual(before,h.state_digest())
 def test_recovery_cannot_expire_unrelated_assignment(self):
  from skynet.coordination import RecoveryRequest
  h=System(2,2);h.run('admit');h.scheduler.dispatch_task('admin','t0',0);r=h.rows()['t0'];h.workers.assign('admin',r[8],'t0','d0','cognitive.reason',1,0,5,1)
  h.scheduler.dispatch_task('admin','t1',1);r=h.rows()['t1'];l=h.workers.assign('admin',r[8],'t1','d1','cognitive.reason',1,1,5,1)
  q=RecoveryRequest('recover','t1',1,r[9],l.worker_id,l.lease_id,'admin','RUNNING','ACTIVE','REQUEUE');before=h.coordinator.states('admin');e=h.coordinator.execute(q,5)
  self.assertEqual((e.status,e.reason),('REJECTED','UNRESOLVED_EXPIRY'));self.assertEqual(before,h.coordinator.states('admin'))
