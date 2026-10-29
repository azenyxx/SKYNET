from dataclasses import asdict,dataclass
from skynet_sys.canonical import FrozenJSON,digest
from skynet_sys.identity import RuntimeIdentity
from skynet_sys.runtime import Runtime
from skynet_sys.messages import Message
from skynet_sys.capabilities import HostPolicy
from skynet_sys.tasks import TaskRequest
from skynet_sys.evidence import EvidenceReference
from skynet_sys_transport.bus import Bus
from skynet_sys_transport.contracts import Config,Topic
from skynet_sys_transport.authorization import Authority
from skynet_sys_scheduler.scheduler import Scheduler
from skynet_sys_scheduler.contracts import Policy as SchedulerPolicy,OPS
from skynet_sys_workers import Orchestrator,Worker,Limits,TYPES
from skynet_sys_memory import Store,Namespace,Operation
from skynet_sys_verification import Engine,Policy,VerificationRequest,VerificationAssessment
from skynet_sys_recovery import Recovery,Telemetry,Policy as RecoveryPolicy,RestoreAdapter,RestoreRequest,RecoveryExecutor
from .coordination import Coordinator,RecoveryRequest,require
T='2026-10-25T00:00:00.000000Z'
@dataclass(frozen=True)
class ReplayView:
 state_commitment:str
 component_commitments:tuple
 workers:tuple
 records:tuple
 head:str
 boundary:str='TRUSTED_FINAL_SNAPSHOT_AUDIT_V1'
 def state_digest(self):return self.state_commitment

class System:
 """Offline serial host. Original public APIs; no fixture imports."""
 def __init__(self,tasks=20,workers=10,attempts=3):
  require(type(tasks)is int and 1<=tasks<=20 and type(workers)is int and 1<=workers<=10,'CONFIG');self.config=(tasks,workers,attempts)
  caps=('cognitive.reason','system.observe');names=('admin','consumer')+tuple('w'+str(i) for i in range(workers))
  self.identities=tuple(RuntimeIdentity('runtime','node',a,T,caps,FrozenJSON.make({})) for a in names)
  grants=tuple((a,c) for a in names for c in caps)+(('admin','memory.read'),('admin','memory.write'))+tuple(('v'+str(i),'cognitive.verify') for i in range(3))
  self.authority=HostPolicy('unified',grants)
  self.runtime=Runtime('runtime',self.authority);self.runtime.register_node(RuntimeIdentity('runtime','node','node',T,(),FrozenJSON.make({}),'NODE'),T)
  for identity in self.identities:self.runtime.register_worker(identity,T)
  rights=tuple((a,'inspect','admin') for a in names)+(('admin','publish','cognitive.tasks'),('admin','publish','system.audit'),('consumer','subscribe','cognitive.tasks'),('consumer','subscribe','system.audit'))
  self.bus=Bus(Config(queue_limit=512),(Topic('cognitive.tasks',('TASK_ACCEPTED','TASK_COMPLETED','TASK_FAILED')),Topic('system.audit',('EVIDENCE_ATTACHED',))),Authority(self.authority,self.identities,rights));self.bus.subscribe('consumer','cognitive.tasks','tasks',0);self.bus.subscribe('consumer','system.audit','audit',0)
  self.scheduler=Scheduler(self.bus,SchedulerPolicy(tuple(('admin',o) for o in OPS)+tuple(('w'+str(i),'complete') for i in range(workers)),timeout_ticks=5),producer_id='admin')
  members=tuple(('admin','d'+str(i)) for i in range(3))+tuple(('w'+str(i),'d'+str(i%3)) for i in range(workers))
  self.workers=Orchestrator(self.authority,('admin',),members)
  for i in range(workers):
   wid='w'+str(i);self.scheduler.register('admin',self.identities[i+2],1,0);self.workers.register('admin',Worker(wid,TYPES[i%3],caps,'local','d'+str(i%3),Limits(attempts=attempts)),0);self.workers.lifecycle('admin',wid,'AVAILABLE',0)
  self.memory=Store(self.authority,(Namespace('agent','admin',('admin',),('admin',),versions=64),),outbox_limit=256)
  self.engine=Engine(self.authority,(Policy('single','SINGLE_AUTHORIZED',('v0',)),Policy('quorum','QUORUM',('v0','v1','v2'),2),Policy('all','UNANIMOUS',('v0','v1','v2'))))
  self.observer=Recovery(self.authority,('workers','scheduler','memory'),(RecoveryPolicy('observe','ESCALATE'),))
  specs=tuple(('t'+str(i),'d'+str((i%workers)%3),'cognitive.reason',1) for i in range(tasks));self.coordinator=Coordinator(self.scheduler,self.workers,specs)
  self.restorer=RestoreAdapter(self.memory,self.authority);self.recovery=RecoveryExecutor(self.coordinator,self.restorer)
  self.leases={};self.restore_requests={};self.records=();self.head='0'*64;self.frozen=False;self.initial_digest=self.state_digest()
 def rows(self):return self.coordinator.rows('admin')
 def state(self):
  return (self.scheduler.checkpoint('admin').commitment,self.workers.state_digest(),self.memory.digest(),self.engine.state_digest(),self.observer.state_digest(),self.bus.inspect('admin',0).state_digest,tuple(e.audit_commitment for e in self.coordinator.records),tuple(e.audit_commitment for e in self.restorer.records),tuple(e.commitment for e in self.runtime.audit))
 def state_digest(self):return digest('unified-state-v1',self.state())
 def run(self,operation,*args):
  require(not self.frozen,'PARTIAL_TRANSITION_BLOCKED');require(len(self.records)<256,'AUDIT_CAPACITY')
  # Canonicalization and arity/type checks MUST finish before predecessor calls.
  command=FrozenJSON.make({'operation':operation,'args':list(args)})
  arities={'admit':0,'dispatch':1,'recover':3,'complete':1,'verify':2,'checkpoint':1,'control':2,'restore':2,'fault':4,'fail_worker':1,'activate':1}
  if operation in arities:require(len(args)==arities[operation],'COMMAND_ARITY')
  if operation=='dispatch':require(type(args[0])is int and 1<=args[0]<=32,'COMMAND_VALUE')
  elif operation=='control':require(all(type(x)is int and 0<=x<=1000000 for x in args),'COMMAND_VALUE')
  elif operation in arities:require(all(type(x)is str for x in args),'COMMAND_TYPE')
  before=self.state_digest();error='';result=None
  try:result=self._apply(operation,args)
  except (ValueError,TypeError,KeyError) as e:error=type(e).__name__+':'+str(e)
  after=self.state_digest();body=(len(self.records),command.data.decode() if type(command.data)is bytes else command.data,before,after,error,self.head);h=digest('unified-journal-v1',body);self.records+=(body+(h,),);self.head=h
  if error:
   if before!=after:self.frozen=True
   raise ValueError(error)
  return result
 def event(self,kind,task,commitment):
  message=Message('unified:'+str(len(self.records)), 'unified-trace',None,None,'admin',self.bus.config.bus_id,'EVIDENCE_ATTACHED',FrozenJSON.make({'kind':kind,'task_id':task,'commitment':commitment,'verification_status':'UNVERIFIED'}),T,self.bus.config.at(1));self.bus.publish('admin','system.audit',message,0)
 def _apply(self,op,args):
  if op=='admit':
   for start in range(0,self.config[0],16):
    batch=tuple((TaskRequest('t'+str(i),None,'trace','admin','cognitive.reason',FrozenJSON.make({'task':i}),0,'2026-10-25T00:01:00.000000Z','key:'+str(i),T),(),self.config[2]) for i in range(start,min(start+16,self.config[0])))
    self.scheduler.admit('admin',batch,0)
  elif op=='dispatch':
   self.scheduler.dispatch('admin',0,args[0])
   for task,row in self.rows().items():
    if row[11]=='RUNNING' and not any(l.task_id==task and l.attempt==row[7] for l in self.workers.leases.values()):
     domain,cap,cost=self.coordinator.specs[task];l=self.workers.assign('admin',row[8],task,domain,cap,row[7],0,row[10],cost);self.leases[task]=l.lease_id
  elif op=='recover':
   action,task,oid=args;lid=self.leases[task];l=self.workers.leases[lid];row=self.rows()[task];q=RecoveryRequest(oid,task,l.attempt,row[9],l.worker_id,lid,'admin',row[11],l.lease_state,action);e=self.recovery.execute(action,q,0)
   if e.new_lease_id:self.leases[task]=e.new_lease_id
   if e.status!='SUCCESS':raise ValueError(e.status+':'+e.reason)
   return e
  elif op=='complete':
   task=args[0];lid=self.leases[task];l=self.workers.leases[lid];row=self.rows()[task];payload=FrozenJSON.make({'task':task,'worker':l.worker_id,'attempt':l.attempt});h=self.workers.complete(l.worker_id,lid,l.attempt,self.workers.workers[l.worker_id].isolation_domain,payload,0);self.scheduler.complete(l.worker_id,task,row[9],True,0)
   ref=EvidenceReference('result:'+task,l.worker_id,task,h,'local-result',T,'UNVERIFIED');self.memory.transact('admin','result:'+task,(Operation('agent','result:'+task,'CREATE',0,payload,(ref,)),),0);self.event('RESULT_PERSISTED',task,h);return h
  elif op=='verify':
   task,policy=args;lid=self.leases[task];l=self.workers.leases[lid];row=self.rows()[task];record=self.memory.read('admin','agent','result:'+task);h=digest('worker-result-v1',record.payload)
   require(len(record.evidence_refs)==1 and record.evidence_refs[0].subject_id==task and record.evidence_refs[0].producer_id==l.worker_id and record.evidence_refs[0].verification_status=='UNVERIFIED' and l.task_id==task and l.lease_state=='COMPLETED' and row[11]=='SUCCEEDED' and row[8]==l.worker_id and row[7]==l.attempt and self.workers.results[lid]==h and record.evidence_refs[0].artifact_digest==h,'RESULT_BINDING')
   q=VerificationRequest('verify:'+task,task,h,l.worker_id,('STRUCTURE','EVIDENCE'),policy,0);self.engine.open(q,record.payload)
   for j in range({'single':1,'quorum':2,'all':3}[policy]):
    v='v'+str(j);e=EvidenceReference('ve:'+task+':'+v,v,task,h,'structural-result',T,'UNVERIFIED');self.engine.submit(VerificationAssessment('a:'+task+':'+v,q.request_id,v,'PASS',(e,),('STRUCTURAL_ONLY',),0),0)
   decision=self.engine.evaluate(q.request_id,0);self.memory.transact('admin','decision:'+task,(Operation('agent','decision:'+task,'CREATE',0,FrozenJSON.make({'decision':decision.decision_commitment,'result':h})),),0);self.event('DECISION_RECORDED',task,decision.decision_commitment);return decision
  elif op=='checkpoint':
   key=args[0];record=self.memory.read('admin','agent','control');cp=self.memory.snapshot('admin',key);self.restorer.bind_checkpoint('admin',cp,(('agent','control'),));return cp
  elif op=='control':
   value,version=args;self.memory.transact('admin','control:'+str(value),(Operation('agent','control','CREATE' if version==0 else 'UPDATE',version,FrozenJSON.make({'value':value})),),0)
  elif op=='restore':
   cp,oid=args
   if oid in self.restore_requests:
    q=self.restore_requests[oid];require(q.checkpoint_id==cp,'CONFLICTING_RESTORE')
   else:q=RestoreRequest(oid,'admin',self.memory.component_id,cp,self.memory.digest(),'DIAGNOSTIC_FORWARD_V1')
   e=self.recovery.execute('RESTORE_CHECKPOINT',q);require(e.status in ('RESTORED','IDEMPOTENT_NOOP'),'RESTORE_FAILED');self.restore_requests[oid]=q;return e
  elif op=='fault':
   event_id,category,component,source=args;return self.observer.collect('admin',Telemetry(event_id,component,category,'ERROR',0,event_id,FrozenJSON.make({'observed':True,'source_commitment':source})))
  elif op=='fail_worker':
   wid=args[0]
   for l in tuple(self.workers.leases.values()):
    if l.worker_id==wid and l.lease_state=='ACTIVE':
     row=self.rows()[l.task_id];q=RecoveryRequest('failure:'+l.lease_id,l.task_id,l.attempt,row[9],wid,l.lease_id,'admin',row[11],l.lease_state,'REQUEUE');e=self.recovery.execute('REQUEUE',q);require(e.status=='SUCCESS','FAILURE_COORDINATION')
   self.workers.fail_worker('admin',wid,0);self.scheduler.worker_state('admin',wid,'UNAVAILABLE',0)
  elif op=='activate':self.workers.lifecycle('admin',args[0],'AVAILABLE',0);self.scheduler.worker_state('admin',args[0],'AVAILABLE',0)
  else:raise ValueError('OPERATION')
 def replay(self,records=None,expected_head=None):
  """Read-only audit replay against current trusted final snapshot; no execution."""
  records=self.records if records is None else records;expected_head=self.head if expected_head is None else expected_head
  require(type(records)is tuple and len(records)<=256,'REPLAY_BOUND');head='0'*64;previous=self.initial_digest
  for i,e in enumerate(records):
   require(type(e)is tuple and len(e)==7 and e[0]==i and e[5]==head and digest('unified-journal-v1',e[:6])==e[6],'JOURNAL_TAMPERED')
   require(e[2]==previous,'REPLAY_STATE_CHAIN');head=e[6];previous=e[3]
  require(head==expected_head,'JOURNAL_HEAD')
  require(records==self.records and head==self.head,'UNSUPPORTED_HISTORY')
  final=self.state_digest();require(previous==final,'SNAPSHOT_BINDING')
  # Snapshot observations, not a reconstructed mutable execution engine.
  workers=tuple((k,w.commitment) for k,w in sorted(self.workers.workers.items()))
  return ReplayView(final,self.state(),workers,records,head)

def workload():
 import time
 start=time.monotonic();h=System();h.run('control',1,0);h.run('checkpoint','cp1');h.run('control',2,1);restores=[h.run('restore','cp1','restore1')];h.run('checkpoint','cp2');h.run('control',3,3);restores.append(h.run('restore','cp2','restore2'))
 h.run('admit');h.run('dispatch',10);old=[]
 for k in range(4):
  task='t'+str(k);old.append(h.workers.leases[h.leases[task]])
  if k<2:
   wid=old[-1].worker_id;h.run('fail_worker',wid);require(h.workers.workers[wid].lifecycle_state=='UNAVAILABLE','FAULT_NOT_OBSERVED');h.run('fault','failed:'+task,'WORKER_FAILED','workers',h.workers.state_digest());h.run('activate',wid)
  else:h.run('recover','REQUEUE',task,'requeue:'+task)
  h.run('recover','RETRY',task,'retry:'+task)
 for k in (4,5):
  task='t'+str(k);old.append(h.workers.leases[h.leases[task]]);e=h.run('recover','RELEASE_LEASE',task,'release:'+task)
 stale=[]
 for l in old:
  before=h.state_digest()
  try:h.workers.complete(l.worker_id,l.lease_id,l.attempt,h.workers.workers[l.worker_id].isolation_domain,FrozenJSON.make({}),0)
  except ValueError as e:require(str(e)=='LEASE_STATE','WRONG_STALE_REASON');stale.append(l.lease_id)
  else:raise AssertionError('STALE_COMPLETION_ACCEPTED')
  require(h.state_digest()==before,'STALE_MUTATION')
 for k in (0,1,2,3,6,7,8,9):h.run('complete','t'+str(k))
 h.run('dispatch',10)
 for k in range(10,20):h.run('complete','t'+str(k));h.run('verify','t'+str(k),('single','quorum','all')[k%3])
 
 for wid in ('w7','w8','w9'):
  h.run('fail_worker',wid);require(h.workers.workers[wid].lifecycle_state=='UNAVAILABLE','FAULT_NOT_OBSERVED');h.run('fault','failed:'+wid,'WORKER_FAILED','workers',h.workers.state_digest())
 other=h.replay();second=h.replay();require(h.state_digest()==other.state_digest()==second.state_digest(),'REPLAY_MISMATCH')
 evidence={'tasks':len(h.rows()),'workers':len(h.workers.workers),'worker_types':len({w.worker_type for w in h.workers.workers.values()}),'domains':len({w.isolation_domain for w in h.workers.workers.values()}),'verification_requests':len(h.engine.rounds),'participating_verifiers':sorted({a.verifier_id for row in h.engine.rounds.values() for a in row['assessments']}),'faults':len(h.observer.faults),'retries':sum(e.status=='SUCCESS' and e.new_lease_id!='' for e in h.coordinator.records),'requeues':sum(e.status=='SUCCESS' and e.predecessor_calls==('Orchestrator.revoke','Scheduler.recover_assignment') and e.recovery_policy=='REQUEUE' for e in h.coordinator.records),'lease_releases':sum(e.status=='SUCCESS' and e.recovery_policy=='RELEASE_LEASE' for e in h.coordinator.records),'restorations':[dict(asdict(e),audit_commitment=e.audit_commitment) for e in restores],'stale_rejections':stale,'state_digest':h.state_digest(),'replay_digest':other.state_digest(),'second_replay_digest':second.state_digest(),'replay_boundary':other.boundary,'component_digests':h.state()[:6],'journal_head':h.head,'seconds':time.monotonic()-start,'recovery':[dict(asdict(e),audit_commitment=e.audit_commitment) for e in h.coordinator.records],'task_states':{k:v[11] for k,v in h.rows().items()},'result_bindings':[{'request_id':rid,'task_id':row['request'].task_id,'producer_id':row['request'].producer_id,'result_commitment':row['request'].result_commitment,'lease_id':h.leases[row['request'].task_id],'worker_result_commitment':h.workers.results[h.leases[row['request'].task_id]],'memory_content_commitment':h.memory.read('admin','agent','result:'+row['request'].task_id).content_digest,'decision':row['decision'].final_verdict,'decision_commitment':row['decision'].decision_commitment} for rid,row in sorted(h.engine.rounds.items())]}
 require(evidence['tasks']==20 and evidence['verification_requests']==10 and evidence['faults']==5,'WORKLOAD');return evidence
