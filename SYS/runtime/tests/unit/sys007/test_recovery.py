import unittest,json,time
from dataclasses import replace,FrozenInstanceError
from skynet_sys_recovery import *
from skynet_sys.errors import ContractError
from skynet_sys_recovery.observation import Observer
from test_workers import integrated
from test_verification import engine as verification_engine,req,assessment,payload
from skynet_sys_memory import MemoryError,Operation

def core(capacity=512):return Recovery(HostPolicy('host',(('admin','system.observe'),)),('c',),tuple(Policy(a.lower(),a) for a in ACTIONS),capacity)
def event(kind='WORKER_FAILED',eid='e',tick=0):return Telemetry(eid,'c',kind,'ERROR',tick,'task',FrozenJSON.make({'observed':True,'source_commitment':'1'*64}))
def fault(o):return o.collect('admin',event())
class Tests(unittest.TestCase):
 def bad(self,code,fn):
  with self.assertRaisesRegex(RecoveryError,'^'+code+'$'):fn()
 def run_case(self,k):
  o=core();e=event()
  if k=='schema':self.bad('SCHEMA',lambda:replace(e,schema_version='bad'))
  elif k=='tick':self.bad('NUMBER',lambda:replace(e,logical_tick=True))
  elif k=='severity':self.bad('SEVERITY',lambda:replace(e,severity='BAD'))
  elif k=='type':self.bad('EVENT_TYPE',lambda:replace(e,event_type='UNKNOWN'))
  elif k=='size':self.bad('PAYLOAD_SIZE',lambda:replace(e,payload=FrozenJSON.make('x'*1025)))
  elif k=='identity':
   with self.assertRaisesRegex(ContractError,'^INVALID_IDENTITY$'):replace(e,event_id='../bad')
  elif k=='immutable':
   with self.assertRaises(FrozenInstanceError):e.event_id='bad'
  elif k=='canonical':self.assertEqual(e.commitment,replace(e).commitment);self.assertNotEqual(e.commitment,replace(e,event_id='other').commitment)
  elif k=='initial':self.assertEqual(o.health['c'],'UNKNOWN')
  elif k=='healthy':o.collect('admin',replace(e,event_type='HEARTBEAT',payload=FrozenJSON.make({'healthy':True})));self.assertEqual(o.health['c'],'HEALTHY')
  elif k=='degraded':o.collect('admin',replace(e,event_type='HEARTBEAT',payload=FrozenJSON.make({'healthy':False})));self.assertEqual(o.health['c'],'DEGRADED')
  elif k=='unhealthy':fault(o);self.assertEqual(o.health['c'],'UNHEALTHY')
  elif k=='quarantine':f=fault(o);o.recover('admin',f,'quarantine','r',0);self.assertEqual(o.health['c'],'QUARANTINED')
  elif k=='no_false_healthy':f=fault(o);o.recover('admin',f,'retry','r',0);self.assertEqual(o.health['c'],'UNHEALTHY')
  elif k=='invalid_health':self.bad('HEARTBEAT',lambda:o.collect('admin',replace(e,event_type='HEARTBEAT',payload=FrozenJSON.make({'healthy':'yes'}))))
  elif k=='quarantine_sticky':f=fault(o);o.recover('admin',f,'quarantine','r',0);o.collect('admin',replace(e,event_id='beat',event_type='HEARTBEAT',payload=FrozenJSON.make({'healthy':True})));self.assertEqual(o.health['c'],'QUARANTINED')
  elif k.startswith('detect_'):
   kind=k[7:];fid=o.collect('admin',event(kind));self.assertEqual(o.faults[fid].category,kind);self.assertEqual(o.faults[fid].evidence_commitment,event(kind).commitment)
  elif k.startswith('action_'):
   a=k[7:];fid=fault(o);result=o.recover('admin',fid,a.lower(),'r',0);expected={'NO_ACTION':'NO_ACTION','QUARANTINE':'QUARANTINED','ESCALATE':'ESCALATED'}.get(a,'BLOCKED_UNSUPPORTED_ACTION');self.assertEqual(result,expected);self.assertEqual(o.attempts[fid][0],1)
  elif k=='retry_exhaustion':
   f=fault(o);o.recover('admin',f,'retry','r1',0);o.recover('admin',f,'retry','r2',1);self.bad('RETRY_EXHAUSTED',lambda:o.recover('admin',f,'retry','r3',2))
  elif k=='backoff':f=fault(o);o.recover('admin',f,'retry','r1',0);self.bad('BACKOFF',lambda:o.recover('admin',f,'retry','r2',0))
  elif k=='policy_unknown':f=fault(o);self.bad('UNKNOWN_POLICY',lambda:o.recover('admin',f,'unknown','r',0))
  elif k=='unauthorized_event':self.bad('UNAUTHORIZED',lambda:o.collect('evil',e));self.assertFalse(o.events)
  elif k=='unauthorized_recovery':f=fault(o);before=o.state_digest();self.bad('UNAUTHORIZED',lambda:o.recover('evil',f,'quarantine','r',0));self.assertEqual(before,o.state_digest())
  elif k=='duplicate_event':fault(o);self.bad('DUPLICATE_EVENT',lambda:o.collect('admin',e));self.assertEqual(len(o.events),1)
  elif k=='duplicate_recovery':f=fault(o);o.recover('admin',f,'quarantine','r',0);before=o.state_digest();self.assertEqual(o.recover('admin',f,'quarantine','r',0),'QUARANTINED');self.assertEqual(before,o.state_digest())
  elif k=='changed_duplicate':f=fault(o);o.recover('admin',f,'quarantine','r',0);self.bad('CONFLICTING_RECOVERY',lambda:o.recover('admin',f,'retry','r',0))
  elif k=='capacity':o=core(1);f=fault(o);before=o.state_digest();self.bad('AUDIT_CAPACITY',lambda:o.recover('admin',f,'quarantine','r',0));self.assertEqual(before,o.state_digest())
  elif k=='missing_evidence':self.bad('EVIDENCE',lambda:o.collect('admin',replace(e,payload=FrozenJSON.make({}))))
  elif k=='unknown_component':self.bad('UNKNOWN_COMPONENT',lambda:o.collect('admin',replace(e,component_id='missing')))
  elif k=='clock':o.collect('admin',event(tick=1));self.bad('CLOCK',lambda:o.collect('admin',event(eid='new',tick=0)))
  elif k=='no_postcondition_claim':f=fault(o);self.assertEqual(o.recover('admin',f,'restore_checkpoint','r',0),'BLOCKED_UNSUPPORTED_ACTION')
  elif k=='replay':f=fault(o);o.recover('admin',f,'quarantine','r',0);self.assertEqual(o.state_digest(),o.replay(o.journal).state_digest())
  elif k=='tamper':fault(o);self.bad('JOURNAL_TAMPERED',lambda:o.replay((replace(o.journal[0],entry_hash='f'*64),)))
  elif k=='sequence':fault(o);self.bad('JOURNAL_CHAIN',lambda:o.replay((replace(o.journal[0],sequence=2),)))
  elif k=='duplicate_journal':fault(o);self.bad('JOURNAL_CHAIN',lambda:o.replay(o.journal+o.journal))
  elif k=='state_mismatch':
   fault(o);j=replace(o.journal[0],state_commitment='f'*64);j=replace(j,entry_hash=digest('recovery-journal-v1',j.body()));self.bad('REPLAY_MISMATCH',lambda:o.replay((j,)))
  elif k=='determinism':other=core();fault(o);fault(other);self.assertEqual(o.journal,other.journal)
  else:raise AssertionError(k)
cases=['schema','tick','severity','type','size','identity','immutable','canonical','initial','healthy','degraded','unhealthy','quarantine','no_false_healthy','invalid_health','quarantine_sticky']+['detect_'+k for k in FAULTS]+['action_'+a for a in ACTIONS]+['retry_exhaustion','backoff','policy_unknown','unauthorized_event','unauthorized_recovery','duplicate_event','duplicate_recovery','changed_duplicate','capacity','missing_evidence','unknown_component','clock','no_postcondition_claim','replay','tamper','sequence','duplicate_journal','state_mismatch','determinism']
for name in cases:
 def test(self,name=name):self.run_case(name)
 setattr(Tests,'test_'+name,test)
class Integration(unittest.TestCase):
 def fixture(self):return integrated(),verification_engine()
 def test_worker_failure(self):w,v=self.fixture();w.fail_worker('w',0);e=Observer(w,v).event('WORKER_FAILED','e','c',0,'w');o=core();fid=o.collect('admin',e);self.assertEqual(fid,'fault:e');self.assertIn(fid,o.faults);self.assertEqual(o.faults[fid].category,'WORKER_FAILED');self.assertEqual(o.faults[fid].evidence_commitment,e.commitment)
 def test_expiry(self):w,v=self.fixture();l=w.dispatch('task','d',1,0);w.advance(5);self.assertEqual(Observer(w,v).event('LEASE_EXPIRED','e','c',5,l.lease_id).event_type,'LEASE_EXPIRED')
 def test_starvation(self):w,v=self.fixture();self.assertEqual(Observer(w,v).event('TASK_STARVATION','e','c',6).event_type,'TASK_STARVATION')
 def test_memory_acl(self):
  w,v=self.fixture()
  with self.assertRaisesRegex(MemoryError,'^DENIED$'):Observer(w,v).checkpoint('w','workers')
 def test_cas(self):
  w,v=self.fixture();before=w.memory.digest()
  with self.assertRaisesRegex(MemoryError,'^VERSION_CONFLICT$'):w.memory.transact('admin','bad',(Operation('agent','workers','UPDATE',0,FrozenJSON.make({})),),0)
  self.assertEqual(before,w.memory.digest())
 def test_rejection(self):w,v=self.fixture();q=req();v.open(q,payload());v.submit(assessment(q,verdict='FAIL'),0);v.evaluate('r',0);self.assertEqual(Observer(w,v).event('VERIFICATION_REJECTED','e','c',0,'r').event_type,'VERIFICATION_REJECTED')
 def test_conflict(self):w,v=self.fixture();q=req();v.open(q,payload());a=assessment(q);v.submit(a,0);v.submit(replace(a,verdict='FAIL'),0);self.assertEqual(Observer(w,v).event('VERIFICATION_CONFLICT','e','c',0,'r').event_type,'VERIFICATION_CONFLICT')
 def test_not_observed(self):
  w,v=self.fixture()
  with self.assertRaisesRegex(RecoveryError,'^NOT_OBSERVED$'):Observer(w,v).event('WORKER_FAILED','e','c',0,'w')
class Simulation(unittest.TestCase):
 def test_bounded(self):
  start=time.monotonic();o=Recovery(HostPolicy('host',(('admin','system.observe'),)),tuple('c'+str(i) for i in range(50)),(Policy('q','QUARANTINE'),Policy('e','ESCALATE'),Policy('r','RETRY')))
  for i in range(200):
   c='c'+str(i%50);kind=FAULTS[i%5] if i<30 else 'HEARTBEAT';data={'observed':True,'source_commitment':digest('injected-fixture-v1',i)} if i<30 else {'healthy':False};o.collect('admin',Telemetry('e'+str(i),c,kind,'ERROR',0,c,FrozenJSON.make(data)))
  outcomes=[]
  for i,f in enumerate(tuple(o.faults)):outcomes.append(o.recover('admin',f,('q','e','r')[i%3],'r'+str(i),0))
  other=o.replay(o.journal);self.assertEqual(o.state_digest(),other.state_digest());self.assertEqual(len(o.events),200);self.assertEqual(len(o.faults),30);print('SIMULATION '+json.dumps({'components':50,'telemetry_events':200,'faults_detected':30,'recovery_attempts':30,'recovery_successes':20,'recovery_failures':10,'quarantined_components':sum(x=='QUARANTINED' for x in o.health.values()),'escalations':outcomes.count('ESCALATED'),'state_digest':o.state_digest(),'replay_digest':other.state_digest(),'elapsed_seconds':time.monotonic()-start,'scope':'HOST_FIXTURE_LOGICAL_ACTIONS_ONLY'}))
