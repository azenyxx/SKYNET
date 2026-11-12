"""Isolated cycle records; no persistence or operational capabilities."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal
from cognitive_contracts import DTO,CognitiveStateV1,ResourcesV1,TaskBudgetV1,canonical_bytes,require,identifier,digest_text,timestamp
from cognitive_plan_contracts import PlanV1,PlanProgressV1
from cognitive_tool_contracts import ToolRequestV1,IsolatedToolBindingV1,ToolEvidenceV1
from cognitive_verification_contracts import VerificationDecisionV1
from cognitive_knowledge_contracts import KnowledgeProposalV1

Outcome = Literal['ISOLATED_CYCLE_SUCCEEDED','CYCLE_REJECTED','CYCLE_BUDGET_EXHAUSTED','CYCLE_DEPENDENCY_UNAVAILABLE']

@dataclass(frozen=True)
class OrchestrationRequestV1:
    schema_version: Literal['cog-orchestration-request-v1']
    state: CognitiveStateV1
    expected_task_revision: int
    plan: PlanV1
    progress: PlanProgressV1
    tool_request: ToolRequestV1
    binding: IsolatedToolBindingV1 | None
    usage: ResourcesV1
    timestamp: str

    def __post_init__(self):
        require(type(self.schema_version) is str and self.schema_version=='cog-orchestration-request-v1','SCHEMA')
        for value,cls in ((self.state,CognitiveStateV1),(self.plan,PlanV1),(self.progress,PlanProgressV1),(self.tool_request,ToolRequestV1),(self.usage,ResourcesV1)):
            require(type(value) is cls,'INPUT_TYPE')
        require(self.binding is None or type(self.binding) is IsolatedToolBindingV1,'BINDING_TYPE')
        require(type(self.expected_task_revision) is int and 0<=self.expected_task_revision<2**63,'REVISION')
        timestamp(self.timestamp)

@dataclass(frozen=True)
class OrchestrationTraceV1(DTO):
    schema_version: Literal['cog-orchestration-trace-v1']
    task_id: str
    task_revision_before: int
    task_revision_after: int
    plan_id: str
    progress_revision_before: int
    progress_revision_after: int
    step_id: str
    tool_request_commitment: str
    result_commitment: str | None
    evidence_commitment: str | None
    verification_decision_id: str | None
    proposal_id: str | None
    budget_before: TaskBudgetV1
    budget_after: TaskBudgetV1
    execution_attempted: Literal[True,False]
    outcome: Outcome
    timestamp: str

    def __post_init__(self):
        super().__post_init__()
        identifier(self.task_id); identifier(self.step_id); timestamp(self.timestamp)
        for v in (self.plan_id,self.tool_request_commitment,self.result_commitment,self.evidence_commitment,self.verification_decision_id,self.proposal_id):
            if v is not None: digest_text(v)
        require(self.task_revision_after>=self.task_revision_before and self.progress_revision_after>=self.progress_revision_before,'TRACE_REVISION')
        require(self.budget_before.maximum==self.budget_after.maximum,'BUDGET_RESET')
        if self.outcome=='ISOLATED_CYCLE_SUCCEEDED':
            require(all(v is not None for v in (self.result_commitment,self.evidence_commitment,self.verification_decision_id,self.proposal_id)) and self.execution_attempted,'SUCCESS_TRACE')

    @property
    def trace_id(self):
        return sha256(b'SKYNET:COGOrchestrationTraceV1:v1\0'+canonical_bytes(self)).hexdigest()

@dataclass(frozen=True)
class OrchestrationOutcomeV1(DTO):
    schema_version: Literal['cog-orchestration-outcome-v1']
    status: Outcome
    reason: str
    state: CognitiveStateV1 | None
    progress: PlanProgressV1 | None
    evidence: ToolEvidenceV1 | None
    verification: VerificationDecisionV1 | None
    proposal: KnowledgeProposalV1 | None
    trace: OrchestrationTraceV1 | None
    completion_reason: Literal['TRUSTED_COMPLETION_UNAVAILABLE']
    production_authorized: Literal[False]
    trusted_verification: Literal[False]
    persisted: Literal[False]

    def __post_init__(self):
        super().__post_init__()
        if self.status=='ISOLATED_CYCLE_SUCCEEDED':
            require(all(v is not None for v in (self.state,self.progress,self.evidence,self.verification,self.proposal,self.trace)),'SUCCESS_FIELDS')
            require(self.state.task.status=='VERIFYING' and self.state.task.result.verification=='UNVERIFIED','NO_COMPLETION')
            require(self.verification.status=='EVIDENCE_VERIFIED_ISOLATED' and self.proposal.knowledge_category=='COMPUTED_FACT_ISOLATED','SUCCESS_BINDING')
