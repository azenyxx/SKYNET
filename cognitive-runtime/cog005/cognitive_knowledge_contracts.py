"""Bounded proposal data. No memory commit, trusted verdict or world assertion."""
from __future__ import annotations
import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal
from cognitive_contracts import DTO, require, identifier, digest_text, canonical_bytes, _decode, ContractError

KnowledgeCategory = Literal['COMPUTED_FACT_ISOLATED','OBSERVATION_UNTRUSTED','VERIFIED_TRUSTED']

@dataclass(frozen=True)
class KnowledgeEvidenceRefV1(DTO):
    schema_version: Literal['cog-knowledge-evidence-ref-v1']
    input_commitment: str
    request_commitment: str
    result_commitment: str
    evidence_commitment: str
    verification_decision_commitment: str
    provenance_classification: Literal['ISOLATED_COMPUTATION_UNTRUSTED_ORIGIN']

    def __post_init__(self):
        super().__post_init__()
        for v in (self.input_commitment,self.request_commitment,self.result_commitment,
                  self.evidence_commitment,self.verification_decision_commitment):
            digest_text(v)

@dataclass(frozen=True)
class ComputedHashFactV1(DTO):
    schema_version: Literal['cog-computed-hash-fact-v1']
    relation: Literal['SHA256_OF_UTF8_INPUT']
    input_commitment: str
    sha256_hex: str
    input_byte_length: int

    def __post_init__(self):
        super().__post_init__()
        digest_text(self.input_commitment)
        digest_text(self.sha256_hex)
        require(self.input_byte_length<=4096,'CONTENT_BOUND')

@dataclass(frozen=True)
class KnowledgeProposalV1(DTO):
    schema_version: Literal['cog-knowledge-proposal-v1']
    task_id: str
    plan_id: str
    step_id: str
    tool_request_id: str
    plan_progress_revision: int
    knowledge_category: KnowledgeCategory
    provenance_classification: Literal['ISOLATED_COMPUTATION_UNTRUSTED_ORIGIN']
    proposed_content: ComputedHashFactV1
    evidence: KnowledgeEvidenceRefV1
    proposal_revision: Literal[1]
    production_authorized: Literal[False]
    trusted_knowledge: Literal[False]
    persisted: Literal[False]

    def __post_init__(self):
        super().__post_init__()
        for v in (self.task_id,self.step_id,self.tool_request_id): identifier(v)
        digest_text(self.plan_id)
        require(self.knowledge_category=='COMPUTED_FACT_ISOLATED','CLASSIFICATION_FORBIDDEN')
        require(self.proposed_content.input_commitment==self.evidence.input_commitment,'CONTENT_BINDING')
        require(self.provenance_classification==self.evidence.provenance_classification,'PROVENANCE_BINDING')

    @property
    def proposal_id(self):
        return sha256(b'SKYNET:COGKnowledgeProposalV1:v1\0'+canonical_bytes(self)).hexdigest()

@dataclass(frozen=True)
class KnowledgeDecisionV1(DTO):
    schema_version: Literal['cog-knowledge-decision-v1']
    status: Literal['KNOWLEDGE_PROPOSED_ISOLATED','KNOWLEDGE_REJECTED','KNOWLEDGE_DEPENDENCY_UNAVAILABLE']
    reason: Literal['ISOLATED_RELATION_ONLY','INVALID_ORIGINAL_ARTIFACTS','VERIFICATION_REJECTED','MISSING_DEPENDENCY','CLASSIFICATION_FORBIDDEN','INVALID_PROVENANCE']
    proposal: KnowledgeProposalV1 | None
    production_authorized: Literal[False]
    trusted_knowledge: Literal[False]
    persisted: Literal[False]

    def __post_init__(self):
        super().__post_init__()
        good=self.status=='KNOWLEDGE_PROPOSED_ISOLATED'
        require((self.proposal is not None)==good and (self.reason=='ISOLATED_RELATION_ONLY')==good,'DECISION_BINDING')
        require((self.status=='KNOWLEDGE_DEPENDENCY_UNAVAILABLE')==(self.reason=='MISSING_DEPENDENCY'),'DEPENDENCY_BINDING')

def parse_proposal(raw: bytes) -> KnowledgeProposalV1:
    require(type(raw) is bytes and len(raw)<=8192,'PROPOSAL_SIZE')
    def pairs(items):
        d={}
        for k,v in items:
            require(k not in d,'DUPLICATE_FIELD')
            d[k]=v
        return d
    try:
        proposal=_decode(json.loads(raw.decode('utf-8'),object_pairs_hook=pairs),KnowledgeProposalV1)
        require(canonical_bytes(proposal)==raw,'NONCANONICAL')
        return proposal
    except (UnicodeError,json.JSONDecodeError,TypeError,RecursionError):
        raise ContractError('MALFORMED_PROPOSAL') from None
