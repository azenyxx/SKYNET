from dataclasses import dataclass
from .canonical import Contract, VERSION, FrozenJSON, check, timestamp
from .errors import need
TYPES=frozenset(('TASK_SUBMITTED','TASK_ACCEPTED','TASK_REJECTED','TASK_COMPLETED','TASK_FAILED','WORKER_REGISTERED','WORKER_HEARTBEAT','CAPABILITY_DENIED','EVIDENCE_ATTACHED'))
@dataclass(frozen=True)
class Message(Contract):
    message_id:str
    trace_id:str
    correlation_id:str|None
    causation_id:str|None
    producer_id:str
    recipient_id:str
    message_type:str
    payload:FrozenJSON
    created_at:str
    expires_at:str
    schema_version:str=VERSION
    def validate(self):
        need(type(self.message_type) is str and self.message_type in TYPES);check(self.payload,FrozenJSON)
        need(self.created_at<self.expires_at and self.causation_id!=self.message_id)
    def validate_at(self,now):
        self.__post_init__();timestamp(now);need(self.created_at<=now<self.expires_at,'EXPIRED_MESSAGE')
