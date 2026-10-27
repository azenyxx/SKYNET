"""Component-local lease revocation; no scheduler or memory reconciliation claim."""
from copy import deepcopy
from dataclasses import dataclass
from skynet_sys.canonical import digest,ident
from skynet_sys_workers import Orchestrator,WorkerError
class RecoveryContractError(ValueError):pass
def need(ok,code):
 if not ok:raise RecoveryContractError(code)
@dataclass(frozen=True)
class Transition:
 operation_id:str
 recovery_action:str
 target_component:str
 target_object:str
 authorized_actor:str
 pre_state_digest:str
 predecessor_api:str
 predecessor_result:str
 post_state_digest:str
 postcondition_checks:tuple
 status:str
 @property
 def audit_commitment(self):return digest('sys007-transition-v1',tuple(vars(self).values()))
class LeaseRecovery:
 def __init__(self,workers,capacity=32):
  need(type(workers)is Orchestrator,'WORKER_CONTRACT');need(type(capacity)is int and 1<=capacity<=128,'CAPACITY');self.workers=deepcopy(workers);self.capacity=capacity;self.records=()
 def release(self,actor,operation_id,lease_id,tick):
  ident(actor);ident(operation_id);ident(lease_id);need(type(tick)is int and tick>=0,'TICK')
  # Authorization uses the real exported inspection guard, including on retries.
  need(lease_id in self.workers.leases,'UNKNOWN_LEASE');lease=self.workers.leases[lease_id];self.workers.inspect(actor,lease.worker_id)
  previous=next((x for x in self.records if x.operation_id==operation_id),None)
  if previous:
   need(previous.authorized_actor==actor and previous.target_object==lease_id,'CONFLICTING_REQUEST');need(self.workers.leases[lease_id].lease_state=='REVOKED','POSTCONDITION');return ('IDEMPOTENT_NOOP',previous)
  need(len(self.records)<self.capacity,'AUDIT_CAPACITY');need(lease.lease_state=='ACTIVE','LEASE_STATE');before=self.workers.state_digest()
  self.workers.revoke(actor,lease_id,tick)
  after=self.workers.state_digest();need(self.workers.leases[lease_id].lease_state=='REVOKED' and before!=after,'POSTCONDITION')
  record=Transition(operation_id,'RELEASE_LEASE','SYS005_ORCHESTRATOR',lease_id,actor,before,'Orchestrator.revoke','REVOKED',after,('LEASE_REVOKED','STATE_CHANGED','PREDECESSOR_JOURNAL_RETAINED'),'COMPLETED');self.records+=(record,);return ('COMPLETED',record)
 def restore(self,*args):raise RecoveryContractError('BLOCKED_CONTRACT_NO_RESTORE_API')
