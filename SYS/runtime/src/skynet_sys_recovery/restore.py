from dataclasses import dataclass,asdict
from skynet_sys.canonical import ident,digest
from skynet_sys_memory import Store,MemoryError
from skynet_sys.capabilities import HostPolicy
class RestoreIntegrationError(ValueError):pass
def need(ok,reason):
 if not ok:raise RestoreIntegrationError(reason)
@dataclass(frozen=True)
class RestoreRequest:
 operation_id:str
 authorized_actor:str
 component_id:str
 checkpoint_id:str
 expected_current_state_digest:str
 restore_policy:str
 def __post_init__(self):
  for v in (self.operation_id,self.authorized_actor,self.component_id,self.checkpoint_id,self.restore_policy):ident(v)
  need(type(self.expected_current_state_digest)is str and len(self.expected_current_state_digest)==64 and all(c in '0123456789abcdef' for c in self.expected_current_state_digest),'STATE_DIGEST')
@dataclass(frozen=True)
class RestoreEvidence:
 operation_id:str
 checkpoint_id:str
 component_id:str
 pre_state_digest:str
 post_state_digest:str
 restored_content_commitment:str
 authorization_result:str
 predecessor_api:str
 predecessor_result:str
 postcondition_status:str
 status:str
 reason:str
 @property
 def audit_commitment(self):return digest('sys007-restore-evidence-v1',tuple(asdict(self).values()))
class RestoreAdapter:
 def __init__(self,store,policy,capacity=32):
  need(type(store)is Store and type(policy)is HostPolicy,'CONTRACT');need(type(capacity)is int and 1<=capacity<=128,'CAPACITY');self.store=store;self.policy=policy;self.capacity=capacity;self.records=();self._bindings={}
 def authorize(self,actor):need(self.policy.decide(actor,'system.observe',('system.observe',)).decision=='ALLOW','RECOVERY_DENIED')
 def bind_checkpoint(self,actor,snapshot,targets):
  self.authorize(actor);self.store.verify_snapshot(snapshot);need(type(targets)is tuple and len(targets)==snapshot.record_count and 1<=len(targets)<=16,'COVERAGE');need(len(set(targets))==len(targets),'DUPLICATE_TARGET');need(snapshot.snapshot_id not in self._bindings,'CHECKPOINT_BOUND');need(len(self._bindings)<self.capacity,'BINDING_CAPACITY')
  rows=[]
  for ns,key in sorted(targets):
   rec=self.store.read(actor,ns,key);rows.append((ns,key,rec.content_digest,tuple(e.commitment for e in rec.evidence_refs)))
  self._bindings[snapshot.snapshot_id]=(snapshot.commitment,tuple(rows))
 def execute(self,request):
  need(type(request)is RestoreRequest,'REQUEST');request.__post_init__();need(len(self.records)<self.capacity,'AUDIT_CAPACITY');before=self.store.digest();status='REJECTED';reason='';auth='DENIED';pred='NOT_INVOKED';postcondition='NOT_CHECKED';content='0'*64
  try:
   self.authorize(request.authorized_actor);auth='RECOVERY_ALLOWED';need(request.checkpoint_id in self._bindings,'CHECKPOINT_NOT_BOUND');bound,rows=self._bindings[request.checkpoint_id]
   result=self.store.restore_checkpoint(**asdict(request));pred=result.restoration_status;auth=result.authorization_result
   actual=[]
   for ns,key,_,_ in rows:
    rec=self.store.read(request.authorized_actor,ns,key);actual.append((ns,key,rec.content_digest,tuple(e.commitment for e in rec.evidence_refs)))
   content=digest('sys007-restored-content-v1',tuple(actual));ok=(tuple(actual)==rows and result.restored_state_digest==self.store.digest() and result.checkpoint_commitment==bound and result.authorization_result=='ALLOW' and result.operation_id==request.operation_id and result.component_id==request.component_id and result.checkpoint_id==request.checkpoint_id and pred in ('RESTORED','IDEMPOTENT_NOOP') and (before!=self.store.digest() if pred=='RESTORED' else before==self.store.digest()))
   status=pred if ok else 'FAILED_POSTCONDITION';postcondition='PASS' if ok else 'FAIL';reason='' if ok else 'POSTCONDITION'
  except (ValueError,TypeError) as e:
   reason=str(e);status='FAILED_POSTCONDITION' if self.store.digest()!=before else ('BLOCKED_CONTRACT' if reason in ('RESTORE_POLICY','CHECKPOINT_NOT_BOUND','RESTORE_BOUND') else 'REJECTED')
  evidence=RestoreEvidence(request.operation_id,request.checkpoint_id,request.component_id,before,self.store.digest(),content,auth,'Store.restore_checkpoint',pred,postcondition,status,reason);self.records+=(evidence,);return evidence
