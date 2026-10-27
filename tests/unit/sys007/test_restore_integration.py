import unittest,json
from dataclasses import replace,asdict
from skynet_sys_recovery import RestoreAdapter,RestoreRequest,RestoreIntegrationError
from skynet_sys_memory import Store,Namespace,Operation,HostPolicy,FrozenJSON
class RestoreIntegrationTests(unittest.TestCase):
 def fixture(self,**kw):
  s=Store(HostPolicy('memory',(('a','memory.read'),('a','memory.write'),('b','memory.read'))),(Namespace('agent','owner',('a','b'),('a',)),),**kw);s.transact('a','one',(Operation('agent','x','CREATE',0,FrozenJSON.make({'v':1})),),0);cp=s.snapshot('a','cp');a=RestoreAdapter(s,HostPolicy('recovery',(('a','system.observe'),('b','system.observe'))));a.bind_checkpoint('a',cp,(('agent','x'),));s.transact('a','two',(Operation('agent','x','UPDATE',1,FrozenJSON.make({'v':2})),),1);q=RestoreRequest('r','a',s.component_id,'cp',s.digest(),'DIAGNOSTIC_FORWARD_V1');return s,a,q,cp
 def test_live_transition(self):
  s,a,q,cp=self.fixture();e=a.execute(q);self.assertEqual(e.status,'RESTORED');self.assertNotEqual(e.pre_state_digest,e.post_state_digest);print('INTEGRATION_EVIDENCE '+json.dumps(dict(asdict(e),audit_commitment=e.audit_commitment)))
 def test_same_instance(self):
  s,a,q,c=self.fixture();self.assertIs(s,a.store);a.execute(q);self.assertEqual(s.read('a','agent','x').version,3)
 def test_content(self):
  s,a,q,c=self.fixture();e=a.execute(q);self.assertEqual(s.read('a','agent','x').payload.value(),{'v':1});self.assertEqual(e.postcondition_status,'PASS')
 def test_digest(self):
  s,a,q,c=self.fixture();e=a.execute(q);self.assertEqual(e.post_state_digest,s.digest());self.assertNotEqual(e.post_state_digest,c.state_digest)
 def test_memory_denied(self):
  s,a,q,c=self.fixture();before=s.digest();e=a.execute(replace(q,authorized_actor='b'));self.assertEqual((e.status,e.reason),('REJECTED','DENIED'));self.assertEqual(before,s.digest())
 def test_component(self):
  s,a,q,c=self.fixture();e=a.execute(replace(q,component_id='other'));self.assertEqual((e.status,e.reason),('REJECTED','COMPONENT_MISMATCH'));self.assertEqual(s.digest(),q.expected_current_state_digest)
 def test_unknown(self):
  s,a,q,c=self.fixture();e=a.execute(replace(q,checkpoint_id='unknown'));self.assertEqual((e.status,e.reason),('BLOCKED_CONTRACT','CHECKPOINT_NOT_BOUND'));self.assertEqual(s.digest(),q.expected_current_state_digest)
 def test_tampered_checkpoint(self):
  s,a,q,c=self.fixture();v=s._checkpoints['cp'];s._checkpoints['cp']=(replace(c,commitment='f'*64),)+v[1:];e=a.execute(q);self.assertEqual((e.status,e.reason),('REJECTED','SNAPSHOT_TAMPERED'));self.assertEqual(s.digest(),q.expected_current_state_digest)
 def test_stale(self):
  s,a,q,c=self.fixture();e=a.execute(replace(q,expected_current_state_digest='f'*64));self.assertEqual((e.status,e.reason),('REJECTED','CURRENT_STATE_CONFLICT'));self.assertEqual(s.digest(),q.expected_current_state_digest)
 def test_idempotent(self):
  s,a,q,c=self.fixture();a.execute(q);before=s.digest();e=a.execute(q);self.assertEqual(e.status,'IDEMPOTENT_NOOP');self.assertEqual(before,s.digest())
 def test_conflicting_duplicate(self):
  s,a,q,c=self.fixture();a.execute(q);before=s.digest();e=a.execute(replace(q,expected_current_state_digest=before));self.assertEqual((e.status,e.reason),('REJECTED','CONFLICTING_RESTORE'));self.assertEqual(before,s.digest())
 def test_capacity(self):
  s,a,q,c=self.fixture(outbox_limit=4);e=a.execute(q);self.assertEqual((e.status,e.reason),('REJECTED','OUTBOX_CAPACITY'));self.assertEqual(s.digest(),q.expected_current_state_digest)
 def test_policy(self):
  s,a,q,c=self.fixture();e=a.execute(replace(q,restore_policy='FULL_ROLLBACK'));self.assertEqual((e.status,e.reason),('BLOCKED_CONTRACT','RESTORE_POLICY'));self.assertEqual(s.digest(),q.expected_current_state_digest)
 def test_recovery_denied(self):
  s,a,q,c=self.fixture();e=a.execute(replace(q,authorized_actor='evil'));self.assertEqual((e.status,e.reason),('REJECTED','RECOVERY_DENIED'));self.assertEqual(s.digest(),q.expected_current_state_digest)
 def test_adapter_audit_capacity(self):
  s,a,q,c=self.fixture();a.capacity=1;a.execute(replace(q,authorized_actor='evil'))
  with self.assertRaisesRegex(RestoreIntegrationError,'^AUDIT_CAPACITY$'):a.execute(q)
  self.assertEqual(s.digest(),q.expected_current_state_digest)
