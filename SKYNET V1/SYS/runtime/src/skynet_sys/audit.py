from dataclasses import dataclass
from .canonical import Contract, VERSION, integer, digest_text
from .errors import need
@dataclass(frozen=True)
class AuditEvent(Contract):
    event_id:str
    runtime_id:str
    subject_id:str
    sequence:int
    action:str
    input_digest:str
    output_digest:str
    previous_digest:str
    created_at:str
    schema_version:str=VERSION
    def validate(self):
        integer(self.sequence);need(self.action in ('NODE_REGISTERED','WORKER_REGISTERED','TASK_CREATED','TASK_TRANSITION','CAPABILITY_DENIED','MESSAGE_ACCEPTED','CHECKPOINT_CREATED','EVIDENCE_ATTACHED'))
        for x in (self.input_digest,self.output_digest,self.previous_digest):digest_text(x)
