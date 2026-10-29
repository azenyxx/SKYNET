import unittest,time,json
from dataclasses import replace
from skynet_sys_memory import *
from skynet_sys.identity import RuntimeIdentity
from skynet_sys_transport.contracts import Config,Topic
from skynet_sys_transport.authorization import Authority
from skynet_sys_transport.bus import Bus
from skynet_sys_scheduler.scheduler import Scheduler
from skynet_sys_scheduler.contracts import Policy,OPS
T='2026-10-25T00:00:00.000000Z'
def policy():return HostPolicy('host',(('a','memory.read'),('a','memory.write'),('b','memory.read')))
def store(**kw):return Store(policy(),(Namespace('agent','owner',('a','b'),('a',)),),**kw)
def op(k='x',kind='CREATE',v=0,ns='agent',payload=None,ev=()):return Operation(ns,k,kind,v,FrozenJSON.make({} if payload is None else payload),ev)
def ev():return EvidenceReference('e','a','x','a'*64,'test',T,'UNVERIFIED')
def bus(queue=100):
 ids=tuple(RuntimeIdentity('r','n',a,T,('system.observe',),FrozenJSON.make({})) for a in ('a','c'))
 rights=(('a','publish','system.audit'),('c','subscribe','system.audit'),('a','inspect','admin'))
 b=Bus(Config(queue_limit=queue),(Topic('system.audit',('EVIDENCE_ATTACHED',)),),Authority(HostPolicy('bus',(('a','system.observe'),('c','system.observe'))),ids,rights));b.subscribe('c','system.audit','s',0);return b
class Tests(unittest.TestCase):
 def bad(self,c,f):
  with self.assertRaisesRegex(MemoryError,'^'+c+'$'):f()
 def setUp(self):self.s=store()
 def create(self):return self.s.transact('a','t',(op(),),0)
 def test_contract_record(self):self.create();self.assertEqual(self.s.read('a','agent','x').version,1)
 def test_contract_schema(self):self.bad('SCHEMA',lambda:replace(Namespace('agent','a',(),()),schema_version='x'))
 def test_contract_boolean(self):self.bad('NUMBER',lambda:op(v=True))
 def test_contract_payload(self):self.bad('PAYLOAD_SIZE',lambda:op(payload=['x'*3000,'y'*3000]))
 def test_contract_kind(self):self.bad('OPERATION',lambda:op(kind='EXECUTE'))
 def test_contract_immutable(self):
  self.create()
  with self.assertRaises(AttributeError):self.s.read('a','agent','x').version=3
 def test_auth_read(self):self.create();self.bad('DENIED',lambda:self.s.read('evil','agent','x'))
 def test_auth_write(self):self.bad('DENIED',lambda:self.s.transact('b','t',(op(),),0))
 def test_auth_owner(self):self.bad('DENIED',lambda:self.s.transact('owner','t',(op(),),0))
 def test_auth_namespace(self):self.bad('UNKNOWN_NAMESPACE',lambda:self.s.transact('a','t',(op(ns='rsi'),),0))
 def test_auth_class(self):self.bad('NAMESPACE',lambda:Namespace('unknown','a',(),()))
 def test_auth_unavailable(self):
  s=Store(replace(policy(),available=False),self.s.namespaces);self.bad('DENIED',lambda:s.transact('a','t',(op(),),0))
 def test_auth_readonly(self):self.create();self.assertEqual(self.s.read('b','agent','x').owner_id,'a')
 def test_version_update(self):self.create();self.s.transact('a','u',(op(kind='UPDATE',v=1),),1);self.assertEqual(self.s.read('a','agent','x').version,2)
 def test_version_stale(self):self.create();self.bad('VERSION_CONFLICT',lambda:self.s.transact('a','u',(op(kind='UPDATE'),),1))
 def test_version_delete(self):self.create();self.s.transact('a','d',(op(kind='DELETE',v=1),),1);self.assertTrue(self.s.read('a','agent','x').deleted)
 def test_version_resurrection(self):self.create();self.s.transact('a','d',(op(kind='DELETE',v=1),),1);self.bad('DELETED',lambda:self.s.transact('a','u',(op(kind='UPDATE',v=2),),2))
 def test_version_retry(self):h=self.create();self.assertEqual(h,self.create());self.assertEqual(len(self.s._journal),1)
 def test_version_conflicting_retry(self):self.create();self.bad('CONFLICTING_RETRY',lambda:self.s.transact('a','t',(op(payload={'z':1}),),0))
 def test_version_missing(self):self.bad('MISSING',lambda:self.s.transact('a','u',(op(kind='UPDATE'),),0))
 def test_version_exists(self):self.create();self.bad('EXISTS',lambda:self.s.transact('a','u',(op(v=1),),0))
 def test_version_update_delete_race(self):self.create();self.s.transact('a','u',(op(kind='UPDATE',v=1),),1);self.bad('VERSION_CONFLICT',lambda:self.s.transact('a','d',(op(kind='DELETE',v=1),),1))
 def test_atomic_multi(self):self.s.transact('a','t',(op('x'),op('y')),0);self.assertEqual(len(self.s._records),2)
 def test_atomic_rollback(self):before=self.s.digest();self.bad('MISSING',lambda:self.s.transact('a','t',(op('x'),op('y','UPDATE')),0));self.assertEqual(before,self.s.digest());self.assertFalse(self.s._journal)
 def test_atomic_duplicate(self):self.bad('DUPLICATE_SUBJECT',lambda:self.s.transact('a','t',(op(),op()),0))
 def test_atomic_capacity(self):s=Store(policy(),(replace(self.s.namespaces[0],capacity=1),));self.bad('RECORD_CAPACITY',lambda:s.transact('a','t',(op('x'),op('y')),0));self.assertFalse(s._records)
 def test_atomic_versions(self):s=Store(policy(),(replace(self.s.namespaces[0],versions=1),));s.transact('a','t',(op(),),0);self.bad('VERSION_CAPACITY',lambda:s.transact('a','u',(op(kind='UPDATE',v=1),),1))
 def test_atomic_outbox(self):s=store(outbox_limit=1);s.transact('a','t',(op(),),0);self.bad('OUTBOX_CAPACITY',lambda:s.transact('a','u',(op('y'),),0));self.assertEqual(len(s._records),1)
 def test_atomic_journal(self):s=store(journal_limit=1);s.transact('a','t',(op(),),0);self.bad('JOURNAL_CAPACITY',lambda:s.transact('a','u',(op('y'),),0))
 def test_atomic_clock(self):self.s.transact('a','t',(op(),),2);self.bad('CLOCK',lambda:self.s.transact('a','u',(op('y'),),1))
 def test_evidence_preserved(self):self.s.transact('a','t',(op(ev=(ev(),)),),0);self.assertEqual(self.s.read('a','agent','x').evidence_refs,(ev(),))
 def test_evidence_no_promotion(self):self.s.transact('a','t',(op(ev=(ev(),)),),0);self.assertEqual(self.s.read('a','agent','x').evidence_refs[0].verification_status,'UNVERIFIED')
 def test_evidence_duplicates(self):self.bad('EVIDENCE_DUPLICATE',lambda:op(ev=(ev(),ev())))
 def test_evidence_shape(self):self.bad('EVIDENCE',lambda:op(ev=[]))
 def test_evidence_commitment(self):self.assertNotEqual(op(ev=(ev(),)).commitment,op().commitment)
 def test_replay_equal(self):self.create();self.assertEqual(self.s.digest(),self.s.replay('a',self.s._journal).digest())
 def test_replay_tamper(self):self.create();self.bad('JOURNAL_TAMPERED',lambda:self.s.replay('a',(replace(self.s._journal[0],record_hash='0'*64),)))
 def test_replay_order(self):self.create();self.s.transact('a','u',(op('y'),),0);self.bad('JOURNAL_CHAIN',lambda:self.s.replay('a',self.s._journal[::-1]))
 def test_replay_tombstone(self):self.create();self.s.transact('a','d',(op(kind='DELETE',v=1),),1);self.assertTrue(self.s.replay('a',self.s._journal).read('a','agent','x').deleted)
 def test_snapshot_valid(self):self.create();self.s.verify_snapshot(self.s.snapshot('a','snap'))
 def test_snapshot_tamper(self):s=self.s.snapshot('a','snap');self.bad('SNAPSHOT_TAMPERED',lambda:replace(s,record_count=1).verify())
 def test_snapshot_stale(self):s=self.s.snapshot('a','snap');self.create();self.bad('SNAPSHOT_MISMATCH',lambda:self.s.verify_snapshot(s))
 def test_history(self):self.create();self.s.transact('a','u',(op(kind='UPDATE',v=1),),1);self.assertEqual(tuple(r.version for r in self.s.history('a','agent','x')),(1,2))
 def test_compaction(self):self.bad('COMPACTION_UNSAFE',self.s.compact)
 def test_integration_bus(self):self.create();b=bus();self.assertTrue(self.s.flush(b,'a','system.audit',0));self.assertFalse(self.s._outbox)
 def test_integration_backpressure(self):
  self.create();b=bus(queue=1);self.s.flush(b,'a','system.audit',0);self.s.transact('a','u',(op('y'),),0);before=self.s._outbox
  from skynet_sys_transport.contracts import BusError
  with self.assertRaisesRegex(BusError,'^QUEUE_FULL$'):self.s.flush(b,'a','system.audit',0)
  self.assertEqual(before,self.s._outbox);self.assertEqual(len(self.s._records),2)
 def test_integration_checkpoint(self):
  b=bus();s=Scheduler(b,Policy((('a','checkpoint'),)));cp=s.checkpoint('a');self.s.store_checkpoint('a','t','agent','cp',0,cp,0);self.assertEqual(self.s.read('a','agent','cp').payload.value()['commitment'],cp.commitment)
 def test_integration_checkpoint_stale(self):
  s=Scheduler(bus(),Policy((('a','checkpoint'),)));cp=s.checkpoint('a');self.s.store_checkpoint('a','t','agent','cp',0,cp,0);self.bad('VERSION_CONFLICT',lambda:self.s.store_checkpoint('a','u','agent','cp',0,cp,0))
 def test_integration_real_policy(self):self.assertEqual(self.s.policy.decide('b','memory.write',('memory.write',)).decision,'DENY')
 def test_integration_event(self):self.create();self.assertEqual(self.s._outbox[0].value()['events'],['MEMORY_CREATED'])
 def test_load(self):
  start=time.monotonic();s=Store(policy(),tuple(Namespace('agent:'+str(i),'a',('a',),('a',)) for i in range(10)))
  for i in range(100):s.transact('a','c'+str(i),(op(str(i),ns='agent:'+str(i%10)),),0)
  for i in range(100):s.transact('a','u'+str(i),(op(str(i),'UPDATE',1,'agent:'+str(i%10)),),1)
  self.bad('VERSION_CONFLICT',lambda:s.transact('a','conflict',(op('0','UPDATE',1,'agent:0'),),1));cp=s.snapshot('a','load');s.verify_snapshot(cp);r=s.replay('a',s._journal);self.assertEqual(s.digest(),r.digest());print('LOAD '+json.dumps({'records':100,'namespaces':10,'mutations':200,'digest':s.digest(),'replay_equal':True,'seconds':time.monotonic()-start}))

class RegressionTests(unittest.TestCase):
 def setUp(self):
  self.s=store();self.s.transact('a','t',(op(),),0)
 def conflict(self):
  with self.assertRaisesRegex(MemoryError,'^VERSION_CONFLICT$'):self.s.transact('a','stale',(op(kind='UPDATE',v=0),),1)
 def test_conflict_record_journal_clock_unchanged(self):
  before=(self.s.digest(),self.s._records.copy(),self.s._journal,self.s._tick,self.s._seen.copy());self.conflict();self.assertEqual(before,(self.s.digest(),self.s._records,self.s._journal,self.s._tick,self.s._seen))
 def test_conflict_event_contract(self):
  self.conflict();e=self.s._outbox[-1].value();self.assertEqual(e['event'],'MEMORY_CONFLICT');self.assertEqual(e['category'],'VERSION_CONFLICT');self.assertEqual((e['namespace'],e['record_id'],e['expected_version'],e['actual_version']),('agent','x',0,1));self.assertIs(e['mutation_committed'],False)
 def test_conflict_multi_record_rollback(self):
  before=self.s.digest()
  with self.assertRaisesRegex(MemoryError,'^VERSION_CONFLICT$'):self.s.transact('a','multi',(op('y'),op(kind='UPDATE',v=0)),1)
  self.assertEqual(before,self.s.digest());self.assertNotIn(('agent','y'),self.s._records)
 def test_conflict_transport_authorization(self):
  from skynet_sys_transport.contracts import BusError
  b=bus();self.s.flush(b,'a','system.audit',0);self.conflict();before=self.s._outbox
  with self.assertRaisesRegex(BusError,'^CAPABILITY_DENIED$'):self.s.flush(b,'c','system.audit',0)
  self.assertEqual(before,self.s._outbox)
 def test_conflict_backpressure(self):
  from skynet_sys_transport.contracts import BusError
  b=bus(queue=1);self.s.flush(b,'a','system.audit',0);self.conflict();before=(self.s.digest(),self.s._outbox)
  with self.assertRaisesRegex(BusError,'^QUEUE_FULL$'):self.s.flush(b,'a','system.audit',0)
  self.assertEqual(before,(self.s.digest(),self.s._outbox))
 def test_conflict_publication(self):
  b=bus();self.s.flush(b,'a','system.audit',0);self.conflict();self.s.flush(b,'a','system.audit',0);self.assertFalse(self.s._outbox);self.assertEqual(b._s['metrics']['published_total'],2)
 def test_conflict_outbox_saturation(self):
  s=store(outbox_limit=1);s.transact('a','t',(op(),),0);before=(s.digest(),s._outbox)
  with self.assertRaisesRegex(MemoryError,'^OUTBOX_CAPACITY$'):s.transact('a','stale',(op(kind='UPDATE',v=0),),1)
  self.assertEqual(before,(s.digest(),s._outbox))
 def test_conflict_replay_excludes_diagnostic(self):
  self.conflict();r=self.s.replay('a',self.s._journal);self.assertEqual(r.digest(),self.s.digest());self.assertEqual(len(r._outbox),1);self.assertEqual(len(self.s._outbox),2)
 def test_conflict_no_unauthorized_event(self):
  before=self.s._outbox
  with self.assertRaisesRegex(MemoryError,'^DENIED$'):self.s.transact('b','stale',(op(kind='UPDATE'),),1)
  self.assertEqual(before,self.s._outbox)
 def test_malformed_namespace(self):
  from skynet_sys.errors import ContractError
  with self.assertRaises(ContractError):Namespace('../agent','a',(),())
 def test_invalid_transaction_identity(self):
  from skynet_sys.errors import ContractError
  before=(self.s.digest(),self.s._outbox)
  with self.assertRaises(ContractError):self.s.transact('a','../escape',(op('y'),),0)
  self.assertEqual(before,(self.s.digest(),self.s._outbox))
 def test_invalid_evidence_member(self):
  from skynet_sys.errors import ContractError
  with self.assertRaises(ContractError):op(ev=('not-evidence',))
 def test_invalid_evidence_digest(self):
  from skynet_sys.errors import ContractError
  with self.assertRaisesRegex(ContractError,'^INVALID_DIGEST$'):replace(ev(),artifact_digest='synthetic')
 def test_record_schema(self):
  with self.assertRaisesRegex(MemoryError,'^SCHEMA$'):replace(self.s.read('a','agent','x'),schema_version='unknown')
 def test_snapshot_schema(self):
  cp=self.s.snapshot('a','s')
  with self.assertRaisesRegex(MemoryError,'^SCHEMA$'):replace(cp,schema_version='unknown').verify()
 def test_oversized_payload_atomic(self):
  before=self.s.digest()
  with self.assertRaisesRegex(MemoryError,'^PAYLOAD_SIZE$'):self.s.transact('a','u',(op(payload=['x'*3000,'y'*3000]),),0)
  self.assertEqual(before,self.s.digest())
