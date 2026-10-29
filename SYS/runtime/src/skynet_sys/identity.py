from dataclasses import dataclass
from .canonical import Contract, VERSION, FrozenJSON, check
from .capabilities import capabilities
from .errors import need
@dataclass(frozen=True)
class RuntimeIdentity(Contract):
    runtime_id:str
    node_id:str
    worker_id:str
    created_at:str
    capability_set:tuple
    metadata:FrozenJSON
    identity_type:str='WORKER'
    schema_version:str=VERSION
    def validate(self):
        capabilities(self.capability_set);check(self.metadata,FrozenJSON)
        need(type(self.metadata.value()) is dict)
        need(self.identity_type in ('RUNTIME','NODE','WORKER','EVIDENCE_PRODUCER'))
