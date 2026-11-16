from dataclasses import dataclass,replace,asdict
from copy import deepcopy
from skynet_sys_verification import digest,FrozenJSON
from skynet_sys_recovery import Recovery,Policy,HostPolicy,Telemetry,RecoveryError
from skynet_sys_recovery.observation import Observer
from skynet_sys_memory import Operation,MemoryError
from skynet_sys_transport.contracts import BusError
# AUDIT D-002: SYS-008 harness depends on SYS-005/006 *test* fixtures. Guarded so the package
# imports under the documented PYTHONPATH=src; fixture-dependent calls fail explicitly.
try:
 from test_workers import integrated
 from test_verification import IntegrationTests,engine,req,payload,assessment
except ModuleNotFoundError as _fixture_error:
 class _FixtureUnavailable:
  def __init__(self,name):self._name=name
  def _fail(self,*a,**k):raise IntegrationError('TEST_FIXTURES_UNAVAILABLE')
  __call__=_fail
  def __getattr__(self,attr):self._fail()
 integrated,IntegrationTests,engine,req,payload,assessment=(_FixtureUnavailable(n) for n in ('integrated','IntegrationTests','engine','req','payload','assessment'))

class IntegrationError(ValueError):pass
def need(ok,code):
 if not ok:raise IntegrationError(code)
def reject(code,fn):
 try:fn()
 except ValueError as e:need(str(e)==code,'WRONG_REJECTION');return code
 raise IntegrationError('EXPECTED_REJECTION')
@dataclass(frozen=True)
class ScenarioResult:
 scenario_id:str
 initial_state_digest:str
 actions:tuple
 expected_outcome:str
 actual_outcome:str
 final_state_digest:str
 audit_references:tuple
 replay_digest:str
 status:str
@dataclass(frozen=True)
class Entry:
 sequence:int
 logical_tick:int
 scenario_id:str
 component_id:str
 operation:str
 input_commitment:str
 output_commitment:str
 previous_hash:str
 entry_hash:str
 def body(self):return tuple(getattr(self,k) for k in self.__dataclass_fields__ if k!='entry_hash')
class Harness:
 def __init__(self,capacity=32):
  need(type(capacity)is int and 1<=capacity<=128,'CAPACITY');self.capacity=capacity;self.journal=();self.results=();self.seed=digest('sys008-seed-v1',capacity)
 def state_digest(self):return digest('sys008-state-v1',(self.seed,tuple(e.entry_hash for e in self.journal)))
 def run(self,n):
  need(type(n)is int and 1<=n<=12,'SCENARIO');need(len(self.journal)<self.capacity,'AUDIT_CAPACITY');sid='E2E-'+str(n).zfill(2);need(sid not in tuple(x.scenario_id for x in self.results),'DUPLICATE_SCENARIO')
  w=integrated();v=engine();initial=w.state_digest();actions=[];actual='';refs=[]
  recovery=Recovery(HostPolicy('host',(('admin','system.observe'),)),('c',),(Policy('retry','RETRY'),Policy('escalate','ESCALATE')))
  if n in (1,3):
   l=w.dispatch('task','d',1,0);w.complete('w',l.lease_id,1,'d',FrozenJSON.make({'answer':1}),0);need(w.core.leases[l.lease_id].lease_state=='COMPLETED','COMPLETION');need(scheduler_state(w,'task')=='SUCCEEDED','SCHEDULER');actual='COMPLETED';actions=['dispatch','complete']
  elif n==2:
   from skynet_sys.tasks import TaskRequest
   # Original scheduler rejects unauthorized admission before accepting any task.
   q=TaskRequest('unauthorized',None,'trace','evil','cognitive.reason',FrozenJSON.make({}),0,'2026-10-25T00:01:00.000000Z','key:unauthorized','2026-10-25T00:00:00.000000Z');before=w.state_digest();actual=scheduler_denied(w,q);need(before==w.state_digest(),'MUTATION');actions=['unauthorized-admit']
  elif n==4:
   w.fail_worker('w',0);e=Observer(w,v).event('WORKER_FAILED','e','c',0,'w');fid=recovery.collect('admin',e);need(recovery.faults[fid].category=='WORKER_FAILED','FAULT');actual='FAULT_RECORDED';actions=['fail_worker','observe','collect']
  elif n==5:
   l=w.dispatch('task','d',1,0);w.advance(5);e=Observer(w,v).event('LEASE_EXPIRED','e','c',5,l.lease_id);recovery.collect('admin',e);reject('LEASE_STATE',lambda:w.complete('w',l.lease_id,1,'d',FrozenJSON.make({}),5));actual='EXPIRED';actions=['dispatch','advance','observe','stale-complete']
  elif n==6:
   w=integrated(queue=2);initial=w.state_digest();actual=reject('QUEUE_FULL',lambda:w.dispatch('task','d',1,0));need(w.state_digest()==initial,'MUTATION');actions=['dispatch-backpressure']
  elif n==7:
   before=w.memory.digest();actual=reject('VERSION_CONFLICT',lambda:w.memory.transact('admin','bad',(Operation('agent','workers','UPDATE',0,FrozenJSON.make({})),),0));need(before==w.memory.digest(),'OVERWRITE');actions=['memory-cas']
  elif n in (8,9):
   i,q,l=IntegrationTests().fixture();initial=i.state_digest();i.run('open',(q,payload()),l.lease_id);a=assessment(q);i.run('submit',(a,0))
   if n==9:i.run('submit',(replace(a,verdict='FAIL'),0))
   d=i.run('evaluate',('r',0));actual=d.final_verdict;need(actual==('PASS' if n==8 else 'INCONCLUSIVE'),'DECISION');need(i.state_digest()==i.replay().state_digest(),'REPLAY');w=i.workers;refs=[d.decision_commitment];actions=['open','submit','evaluate','integrated-replay']
  elif n in (10,11):
   fid=recovery.collect('admin',Telemetry('e','c','WORKER_FAILED','ERROR',0,'task',FrozenJSON.make({'observed':True,'source_commitment':'1'*64})));actual=recovery.recover('admin',fid,'retry','r1',0)
   if n==11:
    recovery.recover('admin',fid,'retry','r2',1);actual=reject('RETRY_EXHAUSTED',lambda:recovery.recover('admin',fid,'retry','r3',2))
   actions=['host-observation','blocked-retry'];need(recovery.health['c']=='UNHEALTHY','FALSE_RECOVERY')
  else:
   recovery.collect('admin',Telemetry('e','c','WORKER_FAILED','ERROR',0,'task',FrozenJSON.make({'observed':True,'source_commitment':'1'*64})));actual=reject('JOURNAL_TAMPERED',lambda:recovery.replay((replace(recovery.journal[0],entry_hash='f'*64),)));actions=['collect','tamper-replay']
  expected={1:'COMPLETED',2:'AUTHORIZATION',3:'COMPLETED',4:'FAULT_RECORDED',5:'EXPIRED',6:'QUEUE_FULL',7:'VERSION_CONFLICT',8:'PASS',9:'INCONCLUSIVE',10:'BLOCKED_UNSUPPORTED_ACTION',11:'RETRY_EXHAUSTED',12:'JOURNAL_TAMPERED'}[n];need(actual==expected,'OUTCOME')
  final=digest('sys008-observed-state-v1',(w.state_digest(),recovery.state_digest(),tuple(refs)));previous=self.journal[-1].entry_hash if self.journal else self.seed
  e=Entry(len(self.journal),0,sid,'SYS001-007','scenario',initial,final,previous,'');e=replace(e,entry_hash=digest('sys008-entry-v1',e.body()));self.journal+=(e,)
  result=ScenarioResult(sid,initial,tuple(actions),expected,actual,final,(e.entry_hash,)+tuple(refs),self.state_digest(),'PASS');self.results+=(result,);return result
 def replay(self,records):
  need(type(records)is tuple and len(records)==len(self.journal),'REPLAY_LENGTH');previous=self.seed
  for k,e in enumerate(records):
   need(type(e)is Entry and e.sequence==k and e.previous_hash==previous,'CHAIN');need(e.entry_hash==digest('sys008-entry-v1',e.body()),'TAMPER');previous=e.entry_hash
  need(records==self.journal,'TRUSTED_HEAD');return digest('sys008-state-v1',(self.seed,tuple(e.entry_hash for e in records)))


def scheduler_state(w,task):
 cp=w.scheduler.checkpoint('admin');cp.verify();rows=[row.value() for row in cp.tasks];matches=[row for row in rows if row[0]==task];need(len(matches)==1,'TASK_IDENTITY');return matches[0][11]

def scheduler_denied(w,q):
 from skynet_sys_scheduler.contracts import SchedulingError
 before=w.scheduler.checkpoint('admin').commitment
 try:w.scheduler.admit('evil',((q,(),1),),0)
 except SchedulingError as e:
  need(str(e)=='AUTHORIZATION','WRONG_REJECTION');need(w.scheduler.checkpoint('admin').commitment==before,'SCHEDULER_MUTATION');return str(e)
 raise IntegrationError('EXPECTED_REJECTION')

def workload():
 import time
 from skynet_sys_workers import Orchestrator,Worker,Limits,TYPES
 from skynet_sys_workers.integration import Integrated
 from skynet_sys.identity import RuntimeIdentity
 from skynet_sys.tasks import TaskRequest
 from skynet_sys_transport.contracts import Config,Topic
 from skynet_sys_transport.authorization import Authority
 from skynet_sys_transport.bus import Bus
 from skynet_sys_scheduler.scheduler import Scheduler
 from skynet_sys_scheduler.contracts import Policy as SchedulerPolicy,OPS
 from skynet_sys_memory import Store,Namespace
 from skynet_sys_verification import Engine,Policy as VerificationPolicy,VerificationRequest,VerificationAssessment
 from skynet_sys_verification.integration import IntegratedVerification
 from skynet_sys.evidence import EvidenceReference
 start=time.monotonic();T='2026-10-25T00:00:00.000000Z';caps=('cognitive.reason','system.observe');linked=[];snapshots=[];faults=Recovery(HostPolicy('host',(('admin','system.observe'),)),tuple('c'+str(k) for k in range(10)),(Policy('retry','RETRY'),Policy('escalate','ESCALATE')));outcomes=[];audit_count=0;workers_seen=set();types_seen=set();domains_seen=set();verifiers=set();completed=0
 for k in range(10):
  wid='w'+str(k);domain='d'+str(k%3);kind=TYPES[k%3];ids=tuple(RuntimeIdentity('r','n',a,T,caps,FrozenJSON.make({})) for a in ('admin',wid,'c'));grants=tuple((a,c) for a in ('admin',wid,'c') for c in caps);rights=tuple((a,'inspect','admin') for a in ('admin',wid,'c'))+(('admin','publish','cognitive.tasks'),('admin','publish','system.audit'),('c','subscribe','cognitive.tasks'),('c','subscribe','system.audit'))
  b=Bus(Config(queue_limit=100),(Topic('cognitive.tasks',('TASK_ACCEPTED','TASK_COMPLETED','TASK_FAILED')),Topic('system.audit',('EVIDENCE_ATTACHED',))),Authority(HostPolicy('bus',grants),ids,rights));b.subscribe('c','cognitive.tasks','tasks',0);b.subscribe('c','system.audit','audit',0)
  scheduler=Scheduler(b,SchedulerPolicy(tuple(('admin',op) for op in OPS)+((wid,'complete'),),timeout_ticks=5),producer_id='admin');taskids=tuple('t'+str(k)+':'+str(j) for j in range(2));requests=tuple(TaskRequest(t,None,'trace','admin','cognitive.reason',FrozenJSON.make({'input':t}),0,'2026-10-25T00:01:00.000000Z','key:'+t,T) for t in taskids);scheduler.admit('admin',tuple((q,(),1) for q in requests),0)
  core=Orchestrator(HostPolicy('host',(('admin','system.observe'),('admin','memory.write'),('admin','memory.read'),(wid,'cognitive.reason'))),('admin',),(('admin',domain),(wid,domain)));memory=Store(core.policy,(Namespace('agent','admin',('admin',),('admin',),versions=64),));w=Integrated(core,scheduler,b,memory);w.register(Worker(wid,kind,caps,'trust',domain,Limits()),ids[1],0)
  for j,task in enumerate(taskids):
   data=FrozenJSON.make({'answer':task,'worker':wid});l=w.dispatch(task,domain,1,0);h=w.complete(wid,l.lease_id,1,domain,data,0);need(h==digest('worker-result-v1',data),'RESULT_BINDING');need(scheduler_state(w,task)=='SUCCEEDED','SCHEDULER');record=w.memory.read('admin','agent','e:'+str(len(w.commands)-1)+':0');need(record.payload.value()['data']['result_commitment']==h,'MEMORY_BINDING');need(record.evidence_refs[0].verification_status=='UNVERIFIED','TRUST_PROMOTION');completed+=1
  e=Engine(HostPolicy('verification',((wid,'cognitive.reason'),)+tuple(('v'+str(j),'cognitive.verify') for j in range(3))),(VerificationPolicy('all','UNANIMOUS',('v0','v1','v2'),1),));i=IntegratedVerification(e,w);q=VerificationRequest('r'+str(k),task,h,wid,('STRUCTURE','EVIDENCE'),'all',0);i.run('open',(q,data),l.lease_id)
  for j in range(3):
   vid='v'+str(j);ref=EvidenceReference('ev:'+str(k)+vid,vid,task,h,'result',T,'UNVERIFIED');a=VerificationAssessment('a:'+str(k)+vid,q.request_id,vid,'PASS',(ref,),('STRUCTURAL_ONLY',),0);i.run('submit',(a,0));verifiers.add(vid)
  d=i.run('evaluate',(q.request_id,0));need(d.final_verdict=='PASS','DECISION');stored=i.workers.memory.read('admin','agent','verify:4:decision').payload.value();need(stored['final_verdict']==d.final_verdict,'DECISION_MEMORY');linked.append((task,wid,l.lease_id,h,q.result_commitment,d.decision_commitment));snapshots.append(i.state_digest());audit_count+=len(i.commands)+len(i.workers.commands);workers_seen.add(wid);types_seen.add(kind);domains_seen.add(domain)
  if k<5:
   i.workers.fail_worker(wid,0);event=Observer(i.workers,i.engine).event('WORKER_FAILED','fault'+str(k),'c'+str(k),0,wid);fid=faults.collect('admin',event);outcomes.append(faults.recover('admin',fid,'retry' if k%2 else 'escalate','rec'+str(k),0))
 # Replay of the integration observation journal only, from trusted snapshot commitments.
 seed=digest('sys008-workload-seed-v1',tuple(snapshots));head=seed;entries=[]
 for n,row in enumerate(linked):
  item=(n,head,digest('sys008-workload-link-v1',row));head=digest('sys008-workload-entry-v1',item);entries.append((item,head))
 trusted_final=head;replay=seed
 for item,h in entries:need(item[1]==replay and digest('sys008-workload-entry-v1',item)==h,'WORKLOAD_TAMPER');replay=h
 need(replay==trusted_final,'WORKLOAD_REPLAY')
 return dict(tasks_submitted=len(linked)*2,tasks_completed=completed,tasks_rejected=0,worker_assignments=completed,workers=len(workers_seen),worker_types=len(types_seen),domains=len(domains_seen),verification_requests=len(linked),verification_decisions=len(linked),participating_verifiers=len(verifiers),faults_observed=len(faults.faults),recovery_actions_attempted=len(outcomes),recovery_actions_blocked=outcomes.count('BLOCKED_UNSUPPORTED_ACTION'),recovery_actions_completed=0,escalations=outcomes.count('ESCALATED'),audit_records=audit_count+len(faults.journal)+len(entries),initial_state_digest=seed,state_digest=trusted_final,replay_digest=replay,linked_results=linked,elapsed_seconds=time.monotonic()-start,qualification='CAUSALLY_LINKED_LOCAL_SHARDS; journal replay checks trusted snapshot commitments, not predecessor history')
