from dataclasses import dataclass
from .canonical import Contract, VERSION, FrozenJSON, check, integer, digest_text
from .capabilities import capability
from .errors import need
TERMINAL=frozenset(('SUCCEEDED','FAILED','CANCELLED','EXPIRED'))
TRANSITIONS={'CREATED':('VALIDATED','CANCELLED','EXPIRED'),'VALIDATED':('QUEUED','FAILED','CANCELLED','EXPIRED'),'QUEUED':('RUNNING','FAILED','CANCELLED','EXPIRED'),'RUNNING':('SUCCEEDED','FAILED','CANCELLED','EXPIRED')}
STATES=frozenset(TRANSITIONS)|TERMINAL
def transition(old,new):
    need(type(old) is str and type(new) is str and old in STATES and new in STATES,'INVALID_TRANSITION')
    if old in TERMINAL:
        need(new==old,'INVALID_TRANSITION');return False
    need(new in TRANSITIONS[old],'INVALID_TRANSITION');return True
@dataclass(frozen=True)
class TaskRequest(Contract):
    task_id:str
    parent_task_id:str|None
    trace_id:str
    requester_id:str
    capability_required:str
    payload:FrozenJSON
    priority:int
    deadline:str
    idempotency_key:str
    created_at:str
    schema_version:str=VERSION
    def validate(self):
        capability(self.capability_required);check(self.payload,FrozenJSON);integer(self.priority,0,100)
        need(self.created_at<self.deadline and self.parent_task_id!=self.task_id)
@dataclass(frozen=True)
class TaskResult(Contract):
    task_id:str
    attempt_id:str
    trace_id:str
    producer_id:str
    request_digest:str
    status:str
    payload:FrozenJSON
    created_at:str
    verification_status:str='UNVERIFIED'
    schema_version:str=VERSION
    def validate(self):
        digest_text(self.request_digest);need(type(self.status) is str and self.status in TERMINAL);check(self.payload,FrozenJSON)
        need(self.verification_status=='UNVERIFIED','EVIDENCE_UNAVAILABLE')
