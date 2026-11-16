from dataclasses import dataclass
from .canonical import Contract, VERSION, digest_text, ident
from .errors import need
@dataclass(frozen=True)
class EvidenceReference(Contract):
    evidence_id:str
    producer_id:str
    subject_id:str
    artifact_digest:str
    artifact_type:str
    created_at:str
    verification_status:str
    schema_version:str=VERSION
    def validate(self):
        digest_text(self.artifact_digest);ident(self.artifact_type)
        need(self.verification_status in ('UNVERIFIED','VERIFIED','REJECTED','UNAVAILABLE'))
