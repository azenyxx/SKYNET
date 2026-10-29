from dataclasses import dataclass,replace
from copy import deepcopy
from skynet_sys.canonical import FrozenJSON,digest,ident,check
from skynet_sys.capabilities import HostPolicy
from skynet_sys.evidence import EvidenceReference
from skynet_sys.messages import Message
from skynet_sys_transport.contracts import collection_digest
from skynet_sys_scheduler.contracts import Snapshot as SchedulerSnapshot
class MemoryError(ValueError):pass
def need(ok,code):
 if not ok:raise MemoryError(code)
def number(n,lo=0,hi=1000000):need(type(n) is int and lo<=n<=hi,'NUMBER')
def refs(xs):
 need(type(xs) is tuple and len(xs)<=8,'EVIDENCE')
 for e in xs:check(e,EvidenceReference)
 need(len({e.evidence_id for e in xs})==len(xs),'EVIDENCE_DUPLICATE')
@dataclass(frozen=True)
class Namespace:
 name:str
 owner:str
 readers:tuple
 writers:tuple
 capacity:int=128
 versions:int=16
 schema_version:str='sys004-v1'
 def __post_init__(self):
  ident(self.name);ident(self.owner);need(self.name.split(':')[0] in ('cognitive','agent','learning','rsi','system'),'NAMESPACE');need(self.schema_version=='sys004-v1','SCHEMA')
  for xs in (self.readers,self.writers):
   need(type(xs) is tuple and len(xs)<=32 and len(set(xs))==len(xs),'ACL')
   for x in xs:ident(x)
  number(self.capacity,1,256);number(self.versions,1,64)
@dataclass(frozen=True)
class Record:
 record_id:str
 namespace:str
 owner_id:str
 record_type:str
 payload:FrozenJSON
 version:int
 created_tick:int
 updated_tick:int
 evidence_refs:tuple=()
 deleted:bool=False
 schema_version:str='sys004-v1'
 def __post_init__(self):
  for x in (self.record_id,self.namespace,self.owner_id,self.record_type):ident(x)
  need(self.schema_version=='sys004-v1','SCHEMA');check(self.payload,FrozenJSON);need(len(self.payload.data)<=4096,'PAYLOAD_SIZE');number(self.version,1);number(self.created_tick);number(self.updated_tick);need(self.updated_tick>=self.created_tick,'CLOCK');refs(self.evidence_refs);need(type(self.deleted) is bool,'DELETED')
 @property
 def content_digest(self):return digest('memory-content-v1',self.payload)
 @property
 def commitment(self):return digest('memory-record-v1',(self.schema_version,self.record_id,self.namespace,self.owner_id,self.record_type,self.content_digest,self.version,self.created_tick,self.updated_tick,tuple(e.commitment for e in self.evidence_refs),self.deleted))
@dataclass(frozen=True)
class Operation:
 namespace:str
 record_id:str
 kind:str
 expected_version:int
 payload:FrozenJSON
 evidence_refs:tuple=()
 record_type:str='diagnostic'
 def __post_init__(self):
  ident(self.namespace);ident(self.record_id);ident(self.record_type);need(self.kind in ('CREATE','UPDATE','DELETE'),'OPERATION');number(self.expected_version);check(self.payload,FrozenJSON);need(len(self.payload.data)<=4096,'PAYLOAD_SIZE');refs(self.evidence_refs)
 @property
 def commitment(self):return digest('memory-operation-v1',(self.namespace,self.record_id,self.kind,self.expected_version,self.payload,tuple(e.commitment for e in self.evidence_refs),self.record_type))
@dataclass(frozen=True)
class Entry:
 sequence:int
 transaction_id:str
 actor_id:str
 logical_tick:int
 operations:tuple
 previous_hash:str
 state_digest:str
 record_hash:str
 def body(self):return (self.sequence,self.transaction_id,self.actor_id,self.logical_tick,tuple(o.commitment for o in self.operations),self.previous_hash,self.state_digest)
 def verify(self):need(self.record_hash==digest('memory-journal-v1',self.body()),'JOURNAL_TAMPERED')
@dataclass(frozen=True)
class Snapshot:
 snapshot_id:str
 logical_tick:int
 journal_head:str
 record_count:int
 state_digest:str
 commitment:str
 schema_version:str='sys004-v1'
 def body(self):
  ident(self.snapshot_id);number(self.logical_tick);number(self.record_count);need(self.schema_version=='sys004-v1','SCHEMA');return (self.schema_version,self.snapshot_id,self.logical_tick,self.journal_head,self.record_count,self.state_digest)
 def verify(self):need(self.commitment==digest('memory-snapshot-v1',self.body()),'SNAPSHOT_TAMPERED')
class Store:
 def __init__(self,policy,namespaces,*,journal_limit=1024,outbox_limit=1024):
  check(policy,HostPolicy);need(type(namespaces) is tuple and 1<=len(namespaces)<=32,'NAMESPACES')
  for n in namespaces:need(type(n) is Namespace,'NAMESPACE');n.__post_init__()
  need(len({n.name for n in namespaces})==len(namespaces),'NAMESPACE_DUPLICATE');number(journal_limit,1,2048);number(outbox_limit,1,2048)
  self.policy=policy;self.namespaces=namespaces;self.journal_limit=journal_limit;self.outbox_limit=outbox_limit;self._records={};self._journal=();self._seen={};self._outbox=();self._tick=0;self._checkpoints={};self._restore_results={};self._restore_audit=();self._flush_generation=0
  self._seed=digest('memory-seed-v1',(policy.commitment,tuple(digest('memory-namespace-v1',(n.name,n.owner,n.readers,n.writers,n.capacity,n.versions,n.schema_version)) for n in namespaces),journal_limit,outbox_limit))
 def auth(self,actor,namespace,write=False):
  ident(actor);n=next((n for n in self.namespaces if n.name==namespace),None);need(n is not None,'UNKNOWN_NAMESPACE');cap='memory.write' if write else 'memory.read';need(actor in (n.writers if write else n.readers) and self.policy.decide(actor,cap,(cap,)).decision=='ALLOW','DENIED');return n
 def digest(self,records=None,tick=None):
  r=self._records if records is None else records
  return digest('memory-state-v1',(self._seed,self._tick if tick is None else tick,collection_digest('memory-history-v1',tuple((k,tuple(v.commitment for v in r[k])) for k in sorted(r)))))
 def read(self,actor,ns,key):
  self.auth(actor,ns);need((ns,key) in self._records,'MISSING');return self._records[(ns,key)][-1]
 def history(self,actor,ns,key):self.read(actor,ns,key);return self._records[(ns,key)]
 def transact(self,actor,tx,ops,tick):
  ident(tx);ident(actor);number(tick);need(type(ops) is tuple and 1<=len(ops)<=16,'OPERATIONS')
  for o in ops:need(type(o) is Operation,'OPERATION');o.__post_init__();self.auth(actor,o.namespace,True)
  request=digest('memory-transaction-v1',(actor,tick,tuple(o.commitment for o in ops)))
  if tx in self._seen:need(self._seen[tx][0]==request,'CONFLICTING_RETRY');return self._seen[tx][1]
  need(tick>=self._tick,'CLOCK');need(len(self._journal)<self.journal_limit,'JOURNAL_CAPACITY');need(len(self._outbox)<self.outbox_limit,'OUTBOX_CAPACITY');need(len({(o.namespace,o.record_id) for o in ops})==len(ops),'DUPLICATE_SUBJECT');r=dict(self._records)
  for o in ops:
   n=self.auth(actor,o.namespace,True);key=(o.namespace,o.record_id);hist=r.get(key,());old=hist[-1] if hist else None
   if o.expected_version!=(old.version if old else 0):
    # Diagnostic rejection only: no record, clock, dedup or mutation-journal commit.
    event=FrozenJSON.make({'schema_version':'sys004-v1','event':'MEMORY_CONFLICT','category':'VERSION_CONFLICT','transaction_id':tx,'actor_id':actor,'namespace':o.namespace,'record_id':o.record_id,'expected_version':o.expected_version,'actual_version':old.version if old else 0,'logical_tick':tick,'mutation_committed':False})
    self._outbox+=(event,)
    raise MemoryError('VERSION_CONFLICT')
   if o.kind=='CREATE':need(old is None,'EXISTS');need(sum(k[0]==o.namespace for k in r)<n.capacity,'RECORD_CAPACITY')
   else:need(old is not None,'MISSING');need(not old.deleted,'DELETED')
   need(len(hist)<n.versions,'VERSION_CAPACITY')
   rec=Record(o.record_id,o.namespace,old.owner_id if old else actor,o.record_type,o.payload,(old.version if old else 0)+1,old.created_tick if old else tick,tick,o.evidence_refs,o.kind=='DELETE');r[key]=hist+(rec,)
  sd=self.digest(r,tick);e=Entry(len(self._journal)+1,tx,actor,tick,ops,self._journal[-1].record_hash if self._journal else self._seed,sd,'');e=replace(e,record_hash=digest('memory-journal-v1',e.body()))
  event=FrozenJSON.make({'transaction_id':tx,'events':['MEMORY_'+{'CREATE':'CREATED','UPDATE':'UPDATED','DELETE':'DELETED'}[o.kind] for o in ops],'journal_hash':e.record_hash})
  self._records=r;self._tick=tick;self._journal+=(e,);self._seen[tx]=(request,e.record_hash);self._outbox+=(event,);return e.record_hash
 def snapshot(self,actor,name):
  for n in self.namespaces:self.auth(actor,n.name)
  need(name not in self._checkpoints,'CHECKPOINT_EXISTS');need(len(self._checkpoints)<self.journal_limit,'CHECKPOINT_CAPACITY');need(len(self._outbox)<self.outbox_limit,'OUTBOX_CAPACITY');s=Snapshot(name,self._tick,self._journal[-1].record_hash if self._journal else self._seed,len(self._records),self.digest(),'');s=replace(s,commitment=digest('memory-snapshot-v1',s.body()));self._outbox+=(FrozenJSON.make({'event':'SNAPSHOT_CREATED','commitment':s.commitment}),);self._checkpoints[name]=(s,deepcopy(self._records),self._flush_generation,self._seed);return s
 def verify_snapshot(self,s):
  need(type(s) is Snapshot,'SNAPSHOT');s.verify();need(s.state_digest==self.digest() and s.journal_head==(self._journal[-1].record_hash if self._journal else self._seed) and s.logical_tick==self._tick and s.record_count==len(self._records),'SNAPSHOT_MISMATCH')
 def replay(self,actor,entries):
  for n in self.namespaces:self.auth(actor,n.name)
  need(type(entries) is tuple and len(entries)<=self.journal_limit,'JOURNAL_CAPACITY');head=self._seed
  for i,e in enumerate(entries):need(type(e) is Entry,'JOURNAL');e.verify();need(e.sequence==i+1 and e.previous_hash==head,'JOURNAL_CHAIN');head=e.record_hash
  other=Store(self.policy,self.namespaces,journal_limit=self.journal_limit,outbox_limit=self.outbox_limit)
  for e in entries:other.transact(e.actor_id,e.transaction_id,e.operations,e.logical_tick);need(other._journal[-1]==e,'REPLAY_MISMATCH')
  return other
 def compact(self):raise MemoryError('COMPACTION_UNSAFE')
 def flush(self,bus,actor,topic,tick):
  if not self._outbox:return False
  event=self._outbox[0];mid='memory:'+digest('memory-event-v1',event);m=Message(mid,'memory-trace',None,None,actor,bus.config.bus_id,'EVIDENCE_ATTACHED',event,bus.config.at(tick),bus.config.at(tick+1));bus.publish(actor,topic,m,tick);self._outbox=self._outbox[1:];self._flush_generation+=1;return True
 def store_checkpoint(self,actor,tx,ns,key,expected,checkpoint,tick,evidence=()):
  need(type(checkpoint) is SchedulerSnapshot,'CHECKPOINT');checkpoint.verify();payload=FrozenJSON.make({'schema':'sys003-checkpoint-reference-v1','logical_tick':checkpoint.logical_tick,'scheduler_sequence':checkpoint.scheduler_sequence,'transport_digest':checkpoint.transport_digest,'journal_head':checkpoint.journal_head,'initial_digest':checkpoint.initial_digest,'commitment':checkpoint.commitment,'task_count':len(checkpoint.tasks),'worker_count':len(checkpoint.workers)})
  return self.transact(actor,tx,(Operation(ns,key,'CREATE' if expected==0 else 'UPDATE',expected,payload,evidence,'scheduler-checkpoint'),),tick)

 @property
 def component_id(self):return self._seed
 def restoration_records(self,actor):
  for n in self.namespaces:self.auth(actor,n.name)
  return self._restore_audit
 def restore_checkpoint(self,authorized_actor,component_id,checkpoint_id,expected_current_state_digest,restore_policy,operation_id):
  for value in (authorized_actor,component_id,checkpoint_id,operation_id):ident(value)
  for n in self.namespaces:self.auth(authorized_actor,n.name,True);self.auth(authorized_actor,n.name)
  need(component_id==self.component_id,'COMPONENT_MISMATCH');need(restore_policy=='DIAGNOSTIC_FORWARD_V1','RESTORE_POLICY');need(type(expected_current_state_digest)is str and len(expected_current_state_digest)==64 and all(c in '0123456789abcdef' for c in expected_current_state_digest),'STATE_DIGEST')
  request=(authorized_actor,component_id,checkpoint_id,expected_current_state_digest,restore_policy)
  if operation_id in self._restore_results:
   old_request,result=self._restore_results[operation_id];need(old_request==request,'CONFLICTING_RESTORE');return replace(result,restoration_status='IDEMPOTENT_NOOP')
  need(operation_id not in self._seen,'DUPLICATE_OPERATION');need(expected_current_state_digest==self.digest(),'CURRENT_STATE_CONFLICT');need(checkpoint_id in self._checkpoints,'UNKNOWN_CHECKPOINT')
  snapshot,records,generation,owner=self._checkpoints[checkpoint_id];need(type(snapshot)is Snapshot,'CHECKPOINT');snapshot.verify();need(owner==component_id,'COMPONENT_MISMATCH');need(snapshot.state_digest==self.digest(records,snapshot.logical_tick),'CHECKPOINT_CONTENT');need(len(records)==snapshot.record_count,'CHECKPOINT_CONTENT');need(generation==self._flush_generation,'IRREVERSIBLE_EFFECT');need(set(records)==set(self._records),'IRREVERSIBLE_STATE')
  ops=[]
  for key in sorted(records):
   old=records[key][-1];current=self._records[key][-1];old.__post_init__();current.__post_init__();need(not old.deleted and not current.deleted and old.record_type==current.record_type=='diagnostic','IRREVERSIBLE_STATE');need(old.owner_id==current.owner_id,'OWNERSHIP')
   if old.payload!=current.payload or old.evidence_refs!=current.evidence_refs:ops.append(Operation(key[0],key[1],'UPDATE',current.version,old.payload,old.evidence_refs,'diagnostic'))
  need(bool(ops),'NO_STATE_CHANGE');need(len(ops)<=16,'RESTORE_BOUND');need(len(self._restore_audit)<self.journal_limit,'RESTORE_AUDIT_CAPACITY');need(len(self._outbox)+2<=self.outbox_limit,'OUTBOX_CAPACITY')
  draft=deepcopy(self);before=self.digest();draft.transact(authorized_actor,operation_id,tuple(ops),self._tick)
  for key in records:
   restored=draft._records[key][-1];target=records[key][-1];need(restored.payload==target.payload and restored.evidence_refs==target.evidence_refs,'RESTORE_POSTCONDITION')
  after=draft.digest();need(before!=after,'RESTORE_POSTCONDITION');result=RestoreResult(operation_id,component_id,checkpoint_id,before,after,snapshot.commitment,'ALLOW','RESTORED')
  draft._restore_audit+=(result,);draft._restore_results[operation_id]=(request,result);draft._outbox+=(FrozenJSON.make({'event':'MEMORY_RESTORED','operation_id':operation_id,'checkpoint_commitment':snapshot.commitment,'audit_commitment':result.audit_commitment}),)
  self.__dict__.update(draft.__dict__);return result

@dataclass(frozen=True)
class RestoreResult:
 operation_id:str
 component_id:str
 checkpoint_id:str
 previous_state_digest:str
 restored_state_digest:str
 checkpoint_commitment:str
 authorization_result:str
 restoration_status:str
 @property
 def audit_commitment(self):return digest('memory-restore-v1',tuple(vars(self).values()))
