"""Live, serial host coordination. No distributed atomicity or unsafe rollback."""
from dataclasses import dataclass,asdict
from skynet_sys.canonical import ident,digest
from skynet_sys_scheduler.scheduler import Scheduler
from skynet_sys_workers import Orchestrator
class CoordinationError(ValueError):pass
def require(ok,reason):
 if not ok:raise CoordinationError(reason)
@dataclass(frozen=True)
class RecoveryRequest:
 operation_id:str
 task_id:str
 attempt_id:int
 assignment_id:str
 worker_id:str
 lease_id:str
 authorized_actor:str
 expected_scheduler_state:str
 expected_worker_state:str
 recovery_policy:str
 def __post_init__(self):
  for k,v in asdict(self).items():
   if k!='attempt_id':ident(v)
  require(type(self.attempt_id)is int and 1<=self.attempt_id<=5,'ATTEMPT')
  require(self.recovery_policy in ('RETRY','REQUEUE','RELEASE_LEASE'),'POLICY')
 @property
 def commitment(self):return digest('coordination-request-v1',tuple(asdict(self).values()))
@dataclass(frozen=True)
class CoordinationEvidence:
 operation_id:str
 request_commitment:str
 task_id:str
 attempt_id:int
 assignment_id:str
 lease_id:str
 scheduler_pre_state:str
 worker_pre_state:str
 scheduler_post_state:str
 worker_post_state:str
 predecessor_calls:tuple
 authorization_result:str
 postcondition_result:str
 status:str
 reason:str
 new_lease_id:str
 recovery_policy:str
 previous_hash:str
 @property
 def audit_commitment(self):return digest('coordination-evidence-v1',tuple(asdict(self).values()))
class Coordinator:
 def __init__(self,scheduler,workers,task_specs,capacity=128):
  require(type(scheduler)is Scheduler and type(workers)is Orchestrator,'CONTRACT')
  require(type(task_specs)is tuple and 1<=len(task_specs)<=128,'TASK_SPECS')
  require(type(capacity)is int and 1<=capacity<=512,'CAPACITY')
  self.scheduler=scheduler;self.workers=workers;self.specs={};self.capacity=capacity;self.records=();self.seen={};self.blocked=False
  for task,domain,cap,cost in task_specs:
   for v in (task,domain,cap):ident(v)
   require(task not in self.specs and type(cost)is int and 1<=cost<=10000,'TASK_SPECS');self.specs[task]=(domain,cap,cost)
 def rows(self,actor):
  cp=self.scheduler.checkpoint(actor);cp.verify();rows={}
  for f in cp.tasks:
   v=f.value();require(type(v)is list and len(v)==14,'SCHEDULER_LAYOUT');rows[v[0]]=v
  return rows
 def states(self,actor):return self.scheduler.checkpoint(actor).commitment,self.workers.state_digest()
 def authorize(self,actor,action):
  require(actor in self.workers.admins and self.workers.policy.decide(actor,'system.observe',('system.observe',)).decision=='ALLOW','AUTHORIZATION')
  require((actor,'recover') in self.scheduler.policy.grants,'AUTHORIZATION')
  if action=='RETRY':require((actor,'dispatch') in self.scheduler.policy.grants,'AUTHORIZATION')
  self.scheduler.checkpoint(actor) # original authorization including bus identity
 def execute(self,q,tick):
  require(type(q)is RecoveryRequest,'REQUEST');q.__post_init__();require(type(tick)is int and tick>=0,'TICK');self.authorize(q.authorized_actor,q.recovery_policy)
  pin=digest('coordination-command-v1',(q.commitment,tick))
  if q.operation_id in self.seen:
   old,ev=self.seen[q.operation_id];require(old==pin,'CONFLICTING_DUPLICATE');return ev
  require(not self.blocked,'PARTIAL_TRANSITION_BLOCKED');require(len(self.records)<self.capacity,'AUDIT_CAPACITY')
  before=self.states(q.authorized_actor);calls=[];new='';status='REJECTED';reason='';post='NOT_CHECKED'
  try:
   rows=self.rows(q.authorized_actor);require(q.task_id in rows and q.task_id in self.specs,'UNKNOWN_TASK');row=rows[q.task_id]
   require(q.lease_id in self.workers.leases,'UNKNOWN_LEASE');lease=self.workers.leases[q.lease_id]
   require((lease.task_id,lease.worker_id,lease.attempt)==(q.task_id,q.worker_id,q.attempt_id),'LEASE_BINDING')
   require((row[8],row[9],row[7])==(q.worker_id,q.assignment_id,q.attempt_id),'STALE_ASSIGNMENT')
   require(row[11]==q.expected_scheduler_state and lease.lease_state==q.expected_worker_state,'STATE_CONFLICT')
   require(tick>=self.workers.tick and tick>=self.scheduler.checkpoint(q.authorized_actor).logical_tick,'CLOCK')
   require(not any(r[0]!=q.task_id and r[11]=='RUNNING' and (r[10]<=tick or r[5]<=tick) for r in rows.values()) and not any(l.task_id!=q.task_id and l.lease_state=='ACTIVE' and l.expires_tick<=tick for l in self.workers.leases.values()),'UNRESOLVED_EXPIRY')
   if q.recovery_policy=='RETRY':
    require(row[11]=='READY' and row[12] in ('WORKER_FAILED','ASSIGNMENT_TIMEOUT'),'RETRY_STATE')
    require(lease.lease_state in ('REVOKED','EXPIRED'),'RETRY_STATE');require(row[7]<row[6],'RETRY_BUDGET')
    require(not any(l.task_id==q.task_id and l.lease_state=='ACTIVE' for l in self.workers.leases.values()),'ACTIVE_ASSIGNMENT')
    self.scheduler.dispatch_task(q.authorized_actor,q.task_id,tick);calls.append('Scheduler.dispatch_task')
    current=self.rows(q.authorized_actor)[q.task_id];require(current[11]=='RUNNING' and current[7]==row[7]+1 and current[9]!=row[9],'SCHEDULER_POSTCONDITION')
    domain,cap,cost=self.specs[q.task_id];l=self.workers.assign(q.authorized_actor,current[8],q.task_id,domain,cap,current[7],tick,current[10]-tick,cost);calls.append('Orchestrator.assign');new=l.lease_id
    require(l.attempt==current[7] and l.worker_id==current[8] and l.lease_state=='ACTIVE','WORKER_POSTCONDITION')
   else:
    require(row[11]=='RUNNING' and lease.lease_state=='ACTIVE','RECOVERY_STATE');require(tick<row[10] and tick<lease.expires_tick,'STALE_ASSIGNMENT')
    self.workers.revoke(q.authorized_actor,q.lease_id,tick);calls.append('Orchestrator.revoke')
    self.scheduler.recover_assignment(q.authorized_actor,q.task_id,q.assignment_id,q.attempt_id,q.recovery_policy,tick);calls.append('Scheduler.recover_assignment')
    current=self.rows(q.authorized_actor)[q.task_id];expected='CANCELLED' if q.recovery_policy=='RELEASE_LEASE' else ('READY' if row[7]<row[6] else 'FAILED')
    require(current[11]==expected and self.workers.leases[q.lease_id].lease_state=='REVOKED','POSTCONDITION')
   require(sum(l.task_id==q.task_id and l.lease_state=='ACTIVE' for l in self.workers.leases.values())==(1 if q.recovery_policy=='RETRY' else 0),'ACTIVE_ASSIGNMENT')
   status='SUCCESS';post='PASS'
  except (ValueError,TypeError,KeyError) as e:
   reason=str(e);status='PARTIAL_TRANSITION' if self.states(q.authorized_actor)!=before else 'REJECTED';post='FAIL'
   if status=='PARTIAL_TRANSITION':self.blocked=True
  after=self.states(q.authorized_actor);ev=CoordinationEvidence(q.operation_id,q.commitment,q.task_id,q.attempt_id,q.assignment_id,q.lease_id,*before,*after,tuple(calls),'ALLOW',post,status,reason,new,q.recovery_policy,self.records[-1].audit_commitment if self.records else '0'*64)
  self.records+=(ev,);self.seen[q.operation_id]=(pin,ev);return ev
 def verify_audit(self,records,expected_head):
  require(type(records)is tuple and len(records)<=self.capacity,'AUDIT_BOUND');head='0'*64
  for ev in records:
   require(type(ev)is CoordinationEvidence and ev.previous_hash==head,'AUDIT_CHAIN');head=ev.audit_commitment
  require(head==expected_head,'AUDIT_TAMPER');return head
