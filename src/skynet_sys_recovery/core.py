from dataclasses import dataclass,replace
from copy import deepcopy
from skynet_sys.canonical import FrozenJSON,digest,ident,digest_text,check
from skynet_sys.capabilities import HostPolicy
from skynet_sys_transport.contracts import collection_digest
class RecoveryError(ValueError):pass
def need(ok,code):
 if not ok:raise RecoveryError(code)
def nat(v):need(type(v) is int and 0<=v<=1000000,'NUMBER')
FAULTS=('LEASE_EXPIRED','WORKER_FAILED','TASK_STARVATION','BACKPRESSURE','MEMORY_CONFLICT','VERIFICATION_REJECTED','VERIFICATION_CONFLICT','STALE_HEARTBEAT','INVALID_CHECKPOINT','RETRY_EXHAUSTION')
ACTIONS=('NO_ACTION','RETRY','REQUEUE','QUARANTINE','RELEASE_LEASE','RESTORE_CHECKPOINT','ESCALATE')
HEALTH=('HEALTHY','DEGRADED','UNHEALTHY','RECOVERING','QUARANTINED','UNKNOWN')
@dataclass(frozen=True)
class Telemetry:
 event_id:str
 component_id:str
 event_type:str
 severity:str
 logical_tick:int
 correlation_id:str
 payload:FrozenJSON
 schema_version:str='sys007-v1'
 def __post_init__(self):
  for s in (self.event_id,self.component_id,self.correlation_id):ident(s)
  need(self.event_type in FAULTS+('HEARTBEAT',),'EVENT_TYPE');need(self.severity in ('INFO','WARNING','ERROR','CRITICAL'),'SEVERITY');nat(self.logical_tick);check(self.payload,FrozenJSON);need(len(self.payload.data)<=1024,'PAYLOAD_SIZE');need(self.schema_version=='sys007-v1','SCHEMA')
 @property
 def payload_commitment(self):return digest('recovery-telemetry-payload-v1',self.payload)
 @property
 def commitment(self):return digest('recovery-telemetry-v1',(self.event_id,self.component_id,self.event_type,self.severity,self.logical_tick,self.correlation_id,self.payload_commitment,self.schema_version))
@dataclass(frozen=True)
class Policy:
 policy_id:str
 action:str
 actors:tuple=('admin',)
 attempts:int=2
 backoff:int=1
 def __post_init__(self):
  ident(self.policy_id);need(self.action in ACTIONS,'ACTION');need(type(self.actors) is tuple and 1<=len(self.actors)<=8 and all(type(a) is str for a in self.actors) and len(set(self.actors))==len(self.actors),'ACTORS')
  for a in self.actors:ident(a)
  need(type(self.attempts) is int and 1<=self.attempts<=4,'ATTEMPTS');nat(self.backoff)
@dataclass(frozen=True)
class Fault:
 fault_id:str
 component_id:str
 category:str
 severity:str
 evidence_commitment:str
 logical_tick:int
 classification:str='HOST_OBSERVED_NOT_INDEPENDENT'
@dataclass(frozen=True)
class Journal:
 sequence:int
 logical_tick:int
 fault_id:str
 component_id:str
 policy_id:str
 action:str
 action_result:str
 state_commitment:str
 previous_hash:str
 command_commitment:str
 entry_hash:str
 command:tuple
 def body(self):return (self.sequence,self.logical_tick,self.fault_id,self.component_id,self.policy_id,self.action,self.action_result,self.state_commitment,self.previous_hash,self.command_commitment)
class Recovery:
 def __init__(self,authority,components,policies,capacity=512):
  check(authority,HostPolicy);need(type(components) is tuple and 1<=len(components)<=64 and len(set(components))==len(components),'COMPONENTS')
  for c in components:ident(c)
  need(type(policies) is tuple and 1<=len(policies)<=16,'POLICIES')
  for q in policies:need(type(q) is Policy,'POLICY');q.__post_init__()
  need(len({q.policy_id for q in policies})==len(policies),'POLICIES');need(type(capacity) is int and 1<=capacity<=1024,'CAPACITY')
  self.authority=authority;self.components=components;self.policies=policies;self.capacity=capacity;self.health={c:'UNKNOWN' for c in components};self.beats={};self.events={};self.faults={};self.attempts={};self.results={};self.tick=0;self.journal=();self.seed=digest('recovery-seed-v1',(authority.commitment,components,policies,capacity))
 def state_digest(self):return digest('recovery-state-v1',(self.seed,self.tick,tuple(sorted(self.health.items())),tuple(sorted(self.beats.items())),collection_digest('recovery-events-v1',tuple((k,v.commitment) for k,v in sorted(self.events.items()))),collection_digest('recovery-faults-v1',tuple(sorted(self.faults.items()))),collection_digest('recovery-attempts-v1',tuple(sorted(self.attempts.items()))),collection_digest('recovery-results-v1',tuple(sorted(self.results.items())))))
 def _pre(self,actor,tick):
  nat(tick);need(tick>=self.tick,'CLOCK');need(len(self.journal)<self.capacity,'AUDIT_CAPACITY');need(self.authority.decide(actor,'system.observe',('system.observe',)).decision=='ALLOW','UNAUTHORIZED')
 def _commit(self,op,args,tick,fault='',component='',policy='',action='',result='RECORDED'):
  self.tick=tick;e=Journal(len(self.journal),tick,fault,component,policy,action,result,self.state_digest(),self.journal[-1].entry_hash if self.journal else self.seed,digest('recovery-command-v1',(op,args)),'',(op,args));self.journal+=(replace(e,entry_hash=digest('recovery-journal-v1',e.body())),)
 def collect(self,actor,event):
  need(type(event) is Telemetry,'TELEMETRY');event.__post_init__();self._pre(actor,event.logical_tick);need(event.component_id in self.health,'UNKNOWN_COMPONENT');need(event.event_id not in self.events,'DUPLICATE_EVENT');v=event.payload.value();need(type(v) is dict,'PAYLOAD')
  d=deepcopy(self);c=event.component_id;fid=''
  if event.event_type=='HEARTBEAT':
   need(set(v)=={'healthy'} and type(v['healthy']) is bool,'HEARTBEAT');d.beats[c]=event.logical_tick
   if d.health[c]!='QUARANTINED':d.health[c]='HEALTHY' if v['healthy'] else 'DEGRADED'
  else:
   need(v.get('observed') is True and type(v.get('source_commitment')) is str,'EVIDENCE');digest_text(v['source_commitment']);fid='fault:'+event.event_id;d.faults[fid]=Fault(fid,c,event.event_type,event.severity,event.commitment,event.logical_tick)
   if d.health[c]!='QUARANTINED':d.health[c]='UNHEALTHY'
  d.events[event.event_id]=event;d._commit('collect',(actor,event),event.logical_tick,fid,c);self.__dict__.update(d.__dict__);return fid or None
 def heartbeat_check(self,actor,c,tick,limit):
  self._pre(actor,tick);need(c in self.health,'UNKNOWN_COMPONENT');nat(limit);need(c in self.beats and tick-self.beats[c]>limit,'NOT_STALE');e=Telemetry('stale:'+c+':'+str(tick),c,'STALE_HEARTBEAT','ERROR',tick,c,FrozenJSON.make({'observed':True,'source_commitment':digest('heartbeat-observation-v1',(c,self.beats[c],tick,limit))}));return self.collect(actor,e)
 def recover(self,actor,fid,pid,rid,tick):
  ident(rid);self._pre(actor,tick);need(fid in self.faults,'UNKNOWN_FAULT');policy=next((p for p in self.policies if p.policy_id==pid),None);need(policy is not None,'UNKNOWN_POLICY');need(actor in policy.actors,'UNAUTHORIZED');request=(actor,fid,pid,tick)
  if rid in self.results:need(self.results[rid][0]==request,'CONFLICTING_RECOVERY');return self.results[rid][1]
  n,last=self.attempts.get(fid,(0,-1000000));need(n<policy.attempts,'RETRY_EXHAUSTED');need(tick-last>=policy.backoff,'BACKOFF');d=deepcopy(self);f=d.faults[fid];out='BLOCKED_UNSUPPORTED_ACTION'
  if policy.action=='QUARANTINE':d.health[f.component_id]='QUARANTINED';need(d.health[f.component_id]=='QUARANTINED','POSTCONDITION');out='QUARANTINED'
  elif policy.action=='ESCALATE':out='ESCALATED'
  elif policy.action=='NO_ACTION':out='NO_ACTION'
  # No public predecessor API is bypassed to simulate retry/requeue/restore.
  d.attempts[fid]=(n+1,tick);d.results[rid]=(request,out);d._commit('recover',(actor,fid,pid,rid,tick),tick,fid,f.component_id,pid,policy.action,out);self.__dict__.update(d.__dict__);return out
 def replay(self,entries):
  need(type(entries) is tuple and len(entries)<=self.capacity,'JOURNAL');o=Recovery(self.authority,self.components,self.policies,self.capacity)
  for index,e in enumerate(entries):
   need(type(e) is Journal and e.sequence==index and e.previous_hash==(o.journal[-1].entry_hash if o.journal else o.seed),'JOURNAL_CHAIN');need(e.entry_hash==digest('recovery-journal-v1',e.body()) and e.command_commitment==digest('recovery-command-v1',e.command),'JOURNAL_TAMPERED');op,args=e.command;need(op in ('collect','recover'),'OPERATION');getattr(o,op)(*args);need(o.journal[-1]==e,'REPLAY_MISMATCH')
  return o
