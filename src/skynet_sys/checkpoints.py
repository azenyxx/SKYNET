from dataclasses import dataclass
from .canonical import Contract, VERSION, digest_text, integer
from .errors import need
@dataclass(frozen=True)
class Checkpoint(Contract):
    checkpoint_id:str
    runtime_id:str
    task_id:str
    state_digest:str
    sequence_number:int
    created_at:str
    parent_checkpoint_id:str|None
    schema_version:str=VERSION
    def validate(self):
        digest_text(self.state_digest);integer(self.sequence_number)
        need((self.sequence_number==0)==(self.parent_checkpoint_id is None))
        need(self.parent_checkpoint_id!=self.checkpoint_id)
