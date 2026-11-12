import unittest,json
from dataclasses import replace
from test_memory import store,op,bus
from skynet_sys_memory import MemoryError
class RestoreTests(unittest.TestCase):
 def fixture(self,**kw):
  s=store(**kw);s.transact('a','one',(op(payload={'v':1}),),0);cp=s.snapshot('a','cp');s.transact('a','two',(op(kind='UPDATE',v=1,payload={'v':2}),),1);return s,cp
 def run_restore(self,s,**kw):
  args=dict(authorized_actor='a',component_id=s.component_id,checkpoint_id='cp',expected_current_state_digest=s.digest(),restore_policy='DIAGNOSTIC_FORWARD_V1',operation_id='restore');args.update(kw);return s.restore_checkpoint(**args)
 def test_success_compatibility(self):
  s,cp=self.fixture();r=self.run_restore(s);self.assertEqual(s.read('a','agent','x').payload.value(),{'v':1});self.assertEqual(s.read('a','agent','x').version,3);self.assertEqual(r.restored_state_digest,s.digest());self.assertNotEqual(r.previous_state_digest,r.restored_state_digest);self.assertEqual(r.checkpoint_commitment,cp.commitment);print('RESTORE_EVIDENCE '+json.dumps(dict(vars(r),audit_commitment=r.audit_commitment)))
 def test_authorization(self):
  s,c=self.fixture();before=s.digest()
  with self.assertRaisesRegex(MemoryError,'^DENIED$'):self.run_restore(s,authorized_actor='b')
  self.assertEqual(before,s.digest())
 def test_unknown(self):
  s,c=self.fixture()
  with self.assertRaisesRegex(MemoryError,'^UNKNOWN_CHECKPOINT$'):self.run_restore(s,checkpoint_id='missing')
 def test_tamper(self):
  s,c=self.fixture();v=s._checkpoints['cp'];s._checkpoints['cp']=(replace(c,commitment='f'*64),)+v[1:]
  with self.assertRaisesRegex(MemoryError,'^SNAPSHOT_TAMPERED$'):self.run_restore(s)
 def test_wrong_component(self):
  s,c=self.fixture()
  with self.assertRaisesRegex(MemoryError,'^COMPONENT_MISMATCH$'):self.run_restore(s,component_id='other')
 def test_current_conflict(self):
  s,c=self.fixture()
  with self.assertRaisesRegex(MemoryError,'^CURRENT_STATE_CONFLICT$'):self.run_restore(s,expected_current_state_digest='f'*64)
 def test_irreversible(self):
  s,c=self.fixture();s.transact('a','delete',(op(kind='DELETE',v=2),),1)
  with self.assertRaisesRegex(MemoryError,'^IRREVERSIBLE_STATE$'):self.run_restore(s)
 def test_idempotent(self):
  s,c=self.fixture();expected=s.digest();r=self.run_restore(s);before=s.digest();again=self.run_restore(s,expected_current_state_digest=expected);self.assertEqual(again.restoration_status,'IDEMPOTENT_NOOP');self.assertEqual(before,s.digest());self.assertEqual(len(s.restoration_records('a')),1)
 def test_duplicate_conflict(self):
  s,c=self.fixture();self.run_restore(s)
  with self.assertRaisesRegex(MemoryError,'^CONFLICTING_RESTORE$'):self.run_restore(s)
 def test_atomic_capacity(self):
  s,c=self.fixture(outbox_limit=4);before=(s.digest(),s._journal,s._outbox)
  with self.assertRaisesRegex(MemoryError,'^OUTBOX_CAPACITY$'):self.run_restore(s)
  self.assertEqual(before,(s.digest(),s._journal,s._outbox))
 def test_audit_saturation(self):
  s,c=self.fixture();s._restore_audit=(None,)*s.journal_limit;before=s.digest()
  with self.assertRaisesRegex(MemoryError,'^RESTORE_AUDIT_CAPACITY$'):self.run_restore(s)
  self.assertEqual(before,s.digest())
 def test_invalid_content(self):
  s,c=self.fixture();v=s._checkpoints['cp'];s._checkpoints['cp']=(v[0],{},v[2],v[3])
  with self.assertRaisesRegex(MemoryError,'^CHECKPOINT_CONTENT$'):self.run_restore(s)
 def test_replay_separation(self):
  s,c=self.fixture();self.run_restore(s);replayed=s.replay('a',s._journal);self.assertEqual(replayed.digest(),s.digest());self.assertEqual(replayed.restoration_records('a'),());self.assertEqual(len(s.restoration_records('a')),1)
 def test_published_effect(self):
  s,c=self.fixture();b=bus();s.flush(b,'a','system.audit',1)
  with self.assertRaisesRegex(MemoryError,'^IRREVERSIBLE_EFFECT$'):self.run_restore(s)
