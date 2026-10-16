"""Isolated verification data, never completion or execution capabilities."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal
from cognitive_contracts import DTO, CognitiveStateV1, canonical_bytes, require, digest_text
from cognitive_plan_contracts import PlanV1, PlanProgressV1
from cognitive_tool_contracts import ToolRequestV1, IsolatedToolBindingV1, ToolEvidenceV1

Stage = Literal['INPUT','TASK','PLAN','REQUEST','BINDING','EVIDENCE','RECOMPUTE','COMPLETE']
Code = Literal['INVALID_INPUT','MISSING_DEPENDENCY','INVALID_TASK','INVALID_PLAN','INVALID_REQUEST','INVALID_BINDING','INVALID_EVIDENCE','OUTPUT_MISMATCH','VERIFIED_CONSISTENCY']

@dataclass(frozen=True)
class VerificationRequestV1:
    schema_version: Literal['cog-verification-request-v1']
    state: CognitiveStateV1 | None
    plan: PlanV1 | None
    progress: PlanProgressV1 | None
    request: ToolRequestV1 | None
    binding: IsolatedToolBindingV1 | None
    evidence: ToolEvidenceV1 | None

    def __post_init__(self):
        require(type(self.schema_version) is str and self.schema_version=='cog-verification-request-v1','SCHEMA')
        for value,cls in ((self.state,CognitiveStateV1),(self.plan,PlanV1),(self.progress,PlanProgressV1),(self.request,ToolRequestV1),(self.binding,IsolatedToolBindingV1),(self.evidence,ToolEvidenceV1)):
            require(value is None or type(value) is cls,'INPUT_TYPE')
        # Nested content is revalidated by the verifier at its originating stage.

@dataclass(frozen=True)
class VerificationFindingV1(DTO):
    schema_version: Literal['cog-verification-finding-v1']
    code: Code
    stage: Stage
    severity: Literal['INFO','ERROR']
    description: str

@dataclass(frozen=True)
class VerificationDecisionV1(DTO):
    schema_version: Literal['cog-verification-decision-v1']
    status: Literal['EVIDENCE_VERIFIED_ISOLATED','EVIDENCE_REJECTED','VERIFICATION_DEPENDENCY_UNAVAILABLE']
    findings: tuple[VerificationFindingV1,...]
    original_evidence_commitment: str | None
    original_request_commitment: str | None
    production_authorized: Literal[False]
    trusted_verification: Literal[False]
    task_completion_authorized: Literal[False]

    def __post_init__(self):
        super().__post_init__()
        require(len(self.findings)==1,'FINDINGS')
        positive=self.status=='EVIDENCE_VERIFIED_ISOLATED'
        require((self.original_evidence_commitment is not None)==positive and
                (self.original_request_commitment is not None)==positive,'COMMITMENT_STATUS')
        f=self.findings[0]
        if positive:
            require(f.code=='VERIFIED_CONSISTENCY' and f.stage=='COMPLETE' and f.severity=='INFO','FINDING_STATUS')
            digest_text(self.original_evidence_commitment)
            digest_text(self.original_request_commitment)
        else:
            require(f.severity=='ERROR' and f.code!='VERIFIED_CONSISTENCY','FINDING_STATUS')
            require((f.code=='MISSING_DEPENDENCY')==(self.status=='VERIFICATION_DEPENDENCY_UNAVAILABLE'),'DEPENDENCY_STATUS')

    @property
    def verification_id(self):
        return sha256(b'SKYNET:COGVerificationDecisionV1:v1\0'+canonical_bytes(self)).hexdigest()
