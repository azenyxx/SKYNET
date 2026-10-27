import unittest
from dataclasses import replace
from skynet_sys_workers import *
from skynet_sys_memory import Store,Namespace,MemoryError
from skynet_sys.errors import ContractError
def fixture():
 p=HostPolicy('host',(('admin','system.observe'),('admin','memory.write'),('admin','memory.read'),('w','cognitive.reason')))
 return Orchestrator(p,('admin',),(('admin','d'),('w','d')))
def worker(**kw):return Worker('w','COGNITIVE',('cognitive.reason',),'trust','d',Limits(),**kw)
class Tests(unittest.TestCase):
 def setUp(self):self.o=fixture()
 def ready(self):self.o.register('admin',worker(),0);self.o.lifecycle('admin','w','AVAILABLE',0)
 def lease(self):self.ready();return self.o.assign('admin','w','task','d','cognitive.reason',1,0,5,1)
 def bad(self,c,f):
  with self.assertRaisesRegex(WorkerError,'^'+c+'$'):f()
 def test_register(self):self.o.register('admin',worker(),0);self.assertEqual(self.o.inspect('admin','w').registration_sequence,1)
 def test_duplicate(self):self.ready();self.bad('DUPLICATE_WORKER',lambda:self.o.register('admin',worker(),0))
 def test_schema(self):self.bad('SCHEMA',lambda:worker(schema_version='bad'))
 def test_type(self):self.bad('WORKER_TYPE',lambda:replace(worker(),worker_type='ROOT'))
 def test_capability(self):
  with self.assertRaisesRegex(ContractError,'^CAPABILITY_DENIED$'):replace(worker(),capabilities=('root',))
 def test_limit(self):self.bad('NUMBER',lambda:Limits(active=True))
 def test_forged_registration(self):self.bad('REGISTRATION',lambda:self.o.register('admin',worker(lifecycle_state='AVAILABLE'),0))
 def test_denied_registration(self):self.bad('DENIED',lambda:self.o.register('w',worker(),0))
 def test_denied_activate(self):self.o.register('admin',worker(),0);self.bad('DENIED',lambda:self.o.lifecycle('w','w','AVAILABLE',0))
 def test_unpinned_domain(self):self.bad('ISOLATION',lambda:self.o.register('admin',replace(worker(),isolation_domain='other'),0))
 def test_cross_domain(self):self.ready();self.bad('ISOLATION',lambda:self.o.assign('admin','w','t','other','cognitive.reason',1,0,1,1))
 def test_complete_owner(self):l=self.lease();self.bad('LEASE_OWNER',lambda:self.o.complete('admin',l.lease_id,1,'d',FrozenJSON.make({}),0))
 def test_complete_domain(self):l=self.lease();self.bad('ISOLATION',lambda:self.o.complete('w',l.lease_id,1,'other',FrozenJSON.make({}),0))
 def test_disabled(self):self.ready();self.o.lifecycle('admin','w','DISABLED',0);self.bad('UNAVAILABLE',lambda:self.o.assign('admin','w','t','d','cognitive.reason',1,0,1,1))
 def test_complete(self):l=self.lease();self.o.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0);self.assertEqual(self.o.leases[l.lease_id].lease_state,'COMPLETED')
 def test_duplicate_completion(self):l=self.lease();h=self.o.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0);n=len(self.o.journal);self.assertEqual(h,self.o.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0));self.assertEqual(n,len(self.o.journal))
 def test_expired(self):l=self.lease();self.bad('EXPIRED',lambda:self.o.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),5))
 def test_stale(self):l=self.lease();self.bad('STALE_ATTEMPT',lambda:self.o.complete('w',l.lease_id,2,'d',FrozenJSON.make({}),0))
 def test_cancel(self):l=self.lease();self.o.cancel('admin',l.lease_id,0);self.bad('LEASE_STATE',lambda:self.o.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0))
 def test_expire_advance(self):l=self.lease();self.o.advance('admin',5);self.assertEqual(self.o.leases[l.lease_id].lease_state,'EXPIRED');self.assertEqual(self.o.used['w'],1)
 def test_duration(self):self.ready();self.bad('DURATION',lambda:self.o.assign('admin','w','t','d','cognitive.reason',1,0,11,1))
 def test_budget(self):self.ready();self.bad('BUDGET',lambda:self.o.assign('admin','w','t','d','cognitive.reason',1,0,1,101));self.assertEqual(self.o.used['w'],0)
 def test_active(self):self.lease();self.bad('ACTIVE_LIMIT',lambda:self.o.assign('admin','w','t2','d','cognitive.reason',1,0,1,1))
 def test_unavailable_active_rejected(self):self.lease();self.bad('ACTIVE_LEASE',lambda:self.o.lifecycle('admin','w','UNAVAILABLE',0))
 def test_replay(self):l=self.lease();self.o.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0);self.assertEqual(self.o.state_digest(),self.o.replay('admin',self.o.journal).state_digest())
 def test_tamper(self):self.ready();es=(replace(self.o.journal[0],entry_hash='f'*64),);self.bad('JOURNAL_TAMPERED',lambda:self.o.replay('admin',es))
 def test_reorder(self):self.ready();self.bad('JOURNAL_CHAIN',lambda:self.o.replay('admin',self.o.journal[::-1]))
 def test_memory(self):self.ready();m=Store(self.o.policy,(Namespace('agent','admin',('admin',),('admin',)),));self.o.checkpoint_to_memory('admin',m,'agent','cp',0,'t',0);self.assertEqual(m.read('admin','agent','cp').payload.value()['orchestration_digest'],self.o.state_digest())
 def test_memory_cas(self):
  self.ready();m=Store(self.o.policy,(Namespace('agent','admin',('admin',),('admin',)),));self.o.checkpoint_to_memory('admin',m,'agent','cp',0,'t',0)
  with self.assertRaisesRegex(MemoryError,'^VERSION_CONFLICT$'):self.o.checkpoint_to_memory('admin',m,'agent','cp',0,'u',0)
 def test_memory_denied(self):
  self.ready();m=Store(self.o.policy,(Namespace('agent','admin',(),()),))
  with self.assertRaisesRegex(MemoryError,'^DENIED$'):self.o.checkpoint_to_memory('admin',m,'agent','cp',0,'t',0)

from skynet_sys_workers.integration import Integrated
from skynet_sys.identity import RuntimeIdentity
from skynet_sys.tasks import TaskRequest
from skynet_sys_transport.contracts import Config,Topic,BusError
from skynet_sys_transport.authorization import Authority
from skynet_sys_transport.bus import Bus
from skynet_sys_scheduler.scheduler import Scheduler
from skynet_sys_scheduler.contracts import Policy,OPS
T='2026-10-25T00:00:00.000000Z'
def integrated(queue=100):
 ids=tuple(RuntimeIdentity('r','n',a,T,('cognitive.reason','system.observe'),FrozenJSON.make({})) for a in ('admin','w','c'))
 grants=tuple((a,c) for a in ('admin','w','c') for c in ('cognitive.reason','system.observe'))
 rights=tuple((a,'inspect','admin') for a in ('admin','w','c'))+(('admin','publish','cognitive.tasks'),('admin','publish','system.audit'),('c','subscribe','cognitive.tasks'),('c','subscribe','system.audit'))
 b=Bus(Config(queue_limit=queue),(Topic('cognitive.tasks',('TASK_ACCEPTED','TASK_COMPLETED','TASK_FAILED')),Topic('system.audit',('EVIDENCE_ATTACHED',))),Authority(HostPolicy('bus',grants),ids,rights));b.subscribe('c','cognitive.tasks','tasks',0);b.subscribe('c','system.audit','audit',0)
 sched=Scheduler(b,Policy(tuple(('admin',o) for o in OPS)+(('w','complete'),),timeout_ticks=5),producer_id='admin');q=TaskRequest('task',None,'trace','admin','cognitive.reason',FrozenJSON.make({}),0,'2026-10-25T00:01:00.000000Z','key',T);sched.admit('admin',((q,(),1),),0)
 core=fixture();mem=Store(core.policy,(Namespace('agent','admin',('admin',),('admin',),versions=64),));i=Integrated(core,sched,b,mem);w=replace(worker(),capabilities=ids[1].capability_set);i.register(w,ids[1],0);return i
class Additional(unittest.TestCase):
 def bad(self,c,f):
  with self.assertRaisesRegex(WorkerError,'^'+c+'$'):f()
 def active(self):
  o=fixture();o.register('admin',worker(),0);o.lifecycle('admin','w','AVAILABLE',0);l=o.assign('admin','w','task','d','cognitive.reason',1,0,5,1);return o,l
 def test_revoke(self):o,l=self.active();o.revoke('admin',l.lease_id,0);self.assertEqual(o.leases[l.lease_id].lease_state,'REVOKED')
 def test_revoked_completion(self):o,l=self.active();o.revoke('admin',l.lease_id,0);self.bad('LEASE_STATE',lambda:o.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0))
 def test_worker_failure(self):o,l=self.active();o.fail_worker('admin','w',0);self.assertEqual(o.workers['w'].lifecycle_state,'UNAVAILABLE');self.assertEqual(o.leases[l.lease_id].lease_state,'REVOKED')
 def test_failure_budget(self):o,l=self.active();o.fail_worker('admin','w',0);self.assertEqual(o.used['w'],1)
 def test_revoke_denied(self):o,l=self.active();self.bad('DENIED',lambda:o.revoke('w',l.lease_id,0));self.assertEqual(o.leases[l.lease_id].lease_state,'ACTIVE')
 def test_terminal_revoke(self):o,l=self.active();o.cancel('admin',l.lease_id,0);self.bad('LEASE_STATE',lambda:o.revoke('admin',l.lease_id,0))
 def test_disabled_terminal(self):o=fixture();o.register('admin',worker(),0);o.lifecycle('admin','w','DISABLED',0);self.bad('DISABLED',lambda:o.lifecycle('admin','w','AVAILABLE',0))
 def test_result_conflict(self):o,l=self.active();o.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0);self.bad('CONFLICTING_RESULT',lambda:o.complete('w',l.lease_id,1,'d',FrozenJSON.make({'x':1}),0))
 def test_payload_bound(self):o,l=self.active();self.bad('PAYLOAD_SIZE',lambda:o.complete('w',l.lease_id,1,'d',FrozenJSON.make('x'*1500),0));self.assertEqual(o.leases[l.lease_id].lease_state,'ACTIVE')
 def test_missing_lease(self):o,l=self.active();self.bad('UNKNOWN_LEASE',lambda:o.complete('w','missing',1,'d',FrozenJSON.make({}),0))
 def test_clock(self):o,l=self.active();o.advance('admin',1);self.bad('CLOCK',lambda:o.cancel('admin',l.lease_id,0))
 def test_retry_cap(self):o,l=self.active();o.cancel('admin',l.lease_id,0);self.bad('ATTEMPT',lambda:o.assign('admin','w','task','d','cognitive.reason',2,0,1,1))
 def test_revoke_replay(self):o,l=self.active();o.revoke('admin',l.lease_id,0);self.assertEqual(o.state_digest(),o.replay('admin',o.journal).state_digest())
 def test_failure_replay(self):o,l=self.active();o.fail_worker('admin','w',0);self.assertEqual(o.state_digest(),o.replay('admin',o.journal).state_digest())
 def test_scheduler_complete(self):i=integrated();l=i.dispatch('task','d',1,0);i.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0);self.assertEqual(i.scheduler._state['tasks']['task']['state'],'SUCCEEDED')
 def test_scheduler_ineligible(self):i=integrated();self.bad('TASK_INELIGIBLE',lambda:i.dispatch('missing','d',1,0))
 def test_integration_failure(self):i=integrated();l=i.dispatch('task','d',1,0);i.fail_worker('w',0);self.assertEqual(i.scheduler._state['tasks']['task']['state'],'FAILED')
 def test_integration_expiry(self):i=integrated();l=i.dispatch('task','d',1,0);i.advance(5);self.assertEqual(i.core.leases[l.lease_id].lease_state,'EXPIRED');self.assertEqual(i.scheduler._state['tasks']['task']['state'],'FAILED')
 def test_integration_backpressure(self):
  i=integrated(queue=2);before=i.state_digest()
  with self.assertRaisesRegex(BusError,'^QUEUE_FULL$'):i.dispatch('task','d',1,0)
  self.assertEqual(before,i.state_digest())
 def test_integration_replay(self):i=integrated();l=i.dispatch('task','d',1,0);i.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0);self.assertEqual(i.state_digest(),i.replay().state_digest())
 def test_load(self):
  import time,json
  start=time.monotonic();caps=('cognitive.reason','cognitive.verify');grants=(('admin','system.observe'),)+tuple(('w'+str(k),caps[k%2]) for k in range(50));members=tuple(('admin','d'+str(k)) for k in range(5))+tuple(('w'+str(k),'d'+str(k%5)) for k in range(50));o=Orchestrator(HostPolicy('load',grants),('admin',),members)
  for k in range(50):
   wid='w'+str(k);o.register('admin',Worker(wid,TYPES[k%5],(caps[k%2],),'trust','d'+str(k%5),Limits()),0);o.lifecycle('admin',wid,'AVAILABLE',0)
  for k in range(100):
   wid='w'+str(k%50);l=o.assign('admin',wid,'t'+str(k),'d'+str(k%5),caps[k%2],1,0,5,1)
   if k==98:o.cancel('admin',l.lease_id,0)
   elif k!=99:o.complete(wid,l.lease_id,1,'d'+str(k%5),FrozenJSON.make({'result':k}),0)
  o.advance('admin',5);r=o.replay('admin',o.journal);self.assertEqual(o.state_digest(),r.state_digest());self.assertEqual(len(o.leases),100);print('LOAD '+json.dumps({'workers':50,'types':5,'domains':5,'assignments':100,'completed':98,'cancelled':1,'expired':1,'digest':o.state_digest(),'seconds':time.monotonic()-start}))

class R2Tests(unittest.TestCase):
 def events(self,i):return [m.payload.value() for topic,m in i.bus._s['messages'].values() if topic=='system.audit']
 def test_activation(self):i=integrated();i.fail_worker('w',0);i.activate('w',0);self.assertEqual(i.core.workers['w'].lifecycle_state,'AVAILABLE');self.assertEqual(i.scheduler._state['workers']['w']['status'],'AVAILABLE')
 def test_disable(self):i=integrated();i.disable('w',0);self.assertEqual(i.core.workers['w'].lifecycle_state,'DISABLED');self.assertEqual(self.events(i)[-1]['event'],'WORKER_DISABLED')
 def test_cancel(self):i=integrated();l=i.dispatch('task','d',1,0);i.cancel(l.lease_id,0);self.assertEqual(i.scheduler._state['tasks']['task']['state'],'CANCELLED');self.assertEqual(i.core.leases[l.lease_id].lease_state,'CANCELLED')
 def test_revoke(self):i=integrated();l=i.dispatch('task','d',1,0);i.revoke(l.lease_id,0);self.assertEqual(i.scheduler._state['tasks']['task']['state'],'CANCELLED');self.assertEqual(i.core.leases[l.lease_id].lease_state,'REVOKED')
 def test_zero_expiration(self):i=integrated();before=len(self.events(i));i.advance(1);self.assertEqual(len(self.events(i)),before)
 def test_real_expiration(self):i=integrated();l=i.dispatch('task','d',1,0);i.advance(5);self.assertEqual(self.events(i)[-1]['data']['lease_ids'],[l.lease_id]);self.assertEqual(self.events(i)[-1]['event'],'LEASE_EXPIRED')
 def test_event_order(self):i=integrated();e=self.events(i);self.assertEqual([x['event'] for x in e],['WORKER_REGISTERED','WORKER_AVAILABLE']);self.assertEqual([x['event_index'] for x in e],[0,1])
 def test_cancel_backpressure(self):
  i=integrated();l=i.dispatch('task','d',1,0);i.bus.config=replace(i.bus.config,queue_limit=3);before=i.state_digest()
  with self.assertRaisesRegex(BusError,'^QUEUE_FULL$'):i.cancel(l.lease_id,0)
  self.assertEqual(before,i.state_digest())
 def test_memory_cas_rollback(self):
  from skynet_sys_memory import Operation
  i=integrated();record=i.memory.read('admin','agent','workers');i.memory.transact('admin','external',(Operation('agent','workers','UPDATE',record.version,FrozenJSON.make({})),),0);before=i.state_digest()
  with self.assertRaisesRegex(MemoryError,'^VERSION_CONFLICT$'):i.advance(1)
  self.assertEqual(before,i.state_digest())
 def test_provenance(self):
  from skynet_sys.evidence import EvidenceReference
  i=integrated();l=i.dispatch('task','d',1,0);i.complete('w',l.lease_id,1,'d',FrozenJSON.make({'answer':1}),0)
  for key in ('e:0:0','e:1:0','e:2:0'):
   r=i.memory.read('admin','agent',key);self.assertEqual(type(r.evidence_refs[0]),EvidenceReference);self.assertEqual(r.evidence_refs[0].artifact_digest,digest('worker-provenance-v1',r.payload));self.assertEqual(r.evidence_refs[0].verification_status,'UNVERIFIED')
 def test_revoked_stale_complete(self):
  i=integrated();l=i.dispatch('task','d',1,0);i.revoke(l.lease_id,0);before=i.state_digest()
  with self.assertRaisesRegex(WorkerError,'^LEASE_STATE$'):i.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),0)
  self.assertEqual(before,i.state_digest())
 def test_cancel_idempotent(self):i=integrated();l=i.dispatch('task','d',1,0);i.cancel(l.lease_id,0);before=i.state_digest();i.cancel(l.lease_id,0);self.assertEqual(before,i.state_digest())
 def test_disable_active(self):i=integrated();l=i.dispatch('task','d',1,0);i.disable('w',0);self.assertEqual(i.core.leases[l.lease_id].lease_state,'REVOKED');self.assertEqual([e['event'] for e in self.events(i)][-2:],['LEASE_REVOKED','WORKER_DISABLED'])
 def test_layout_mismatch(self):
  i=integrated();row=i._rows()['task'];i.scheduler._state['tasks']['task']['request']=None
  with self.assertRaisesRegex(WorkerError,'^SCHEDULER_LAYOUT$'):i._capability('task',row)
 def test_integrated_scenario(self):
  import time,json
  start=time.monotonic();old=integrated();core,scheduler,b,memory=old._seed
  for k in ('task2','task3'):
   q=TaskRequest(k,None,'trace','admin','cognitive.reason',FrozenJSON.make({}),0,'2026-10-25T00:01:00.000000Z','key:'+k,T);scheduler.admit('admin',((q,(),1),),0)
  i=Integrated(core,scheduler,b,memory);identity=next(x for x in b.authority.identities if x.worker_id=='w');i.register(replace(worker(),capabilities=identity.capability_set),identity,0);i.fail_worker('w',0);i.activate('w',0)
  l=i.dispatch('task','d',1,0);i.cancel(l.lease_id,0);l=i.dispatch('task2','d',1,0);i.revoke(l.lease_id,0);l=i.dispatch('task3','d',1,0);i.advance(5);i.disable('w',5);self.assertEqual(i.state_digest(),i.replay().state_digest());print('INTEGRATED_LOAD '+json.dumps({'assignments':3,'cancelled':1,'revoked':1,'expired':1,'digest':i.state_digest(),'seconds':time.monotonic()-start}))
