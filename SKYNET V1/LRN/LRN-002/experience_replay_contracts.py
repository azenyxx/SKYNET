"""Immutable diagnostic replay contracts. Commitments do not authenticate origin."""
from dataclasses import dataclass, fields
import learning_foundation as learning
from learning_contracts import need, ident, integer, hashcheck, refs

STRATEGIES = ('SOURCE_SEQUENCE', 'CANONICAL_ID', 'VERIFICATION_PRIORITY')
BLOCKERS = ('L01-001', 'L01-002', 'L01-003', 'L01-004', 'A09-001')


def digest(value):
    return learning.memory.digest('LRN002', value)


def make(cls, **values):
    body = tuple((f.name, values.get(f.name, f.default)) for f in fields(cls) if f.name != 'commitment')
    return cls(**values, commitment=digest(body))


class Contract:
    def __post_init__(self):
        need(self.version == 'lrn002-v1', 'VERSION')
        learning.memory.encoded(self)
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name.endswith('_id'):
                ident(value)
            if f.name.endswith('_commitment'):
                hashcheck(value)
        self.validate()
        need(self.commitment == digest(tuple((f.name, getattr(self, f.name))
             for f in fields(self) if f.name != 'commitment')), 'COMMITMENT')


@dataclass(frozen=True)
class ReplaySource(Contract):
    source_id: str
    record: learning.ExperienceRecord
    evidence: learning.OutcomeEvidence
    assessment: learning.ExperienceAssessment
    verification_inputs: tuple
    source_commitment: str
    commitment: str
    version: str = 'lrn002-v1'

    def validate(self):
        for obj, cls in ((self.record, learning.ExperienceRecord), (self.evidence, learning.OutcomeEvidence),
                         (self.assessment, learning.ExperienceAssessment)):
            need(type(obj) is cls, 'SOURCE_CONTRACT')
            obj.__post_init__()
        need(type(self.verification_inputs) is tuple and len(self.verification_inputs) == 3, 'VERIFICATION_INPUTS')
        need(self.source_commitment == digest((self.record,self.evidence,self.assessment,self.verification_inputs)), 'SOURCE_COMMITMENT')
        need(len(learning.memory.encoded(self)) <= 262144, 'SOURCE_SIZE')


@dataclass(frozen=True)
class SelectionPolicy(Contract):
    policy_id: str
    accepted_trust_classes: tuple
    ordering_strategy: str
    max_batch: int
    per_source: int
    per_task: int
    per_goal: int
    max_operations: int
    resource_ceiling: int
    commitment: str
    version: str = 'lrn002-v1'

    def validate(self):
        refs(self.accepted_trust_classes)
        need(set(self.accepted_trust_classes) <= set(learning.CLASSES)-{'VERIFIED_LOCAL'}, 'TRUST')
        need(self.ordering_strategy in STRATEGIES, 'ORDER')
        for value in (self.max_batch,self.per_source,self.per_task,self.per_goal,self.max_operations,self.resource_ceiling):
            integer(value)
            need(1 <= value <= 64, 'LIMIT')
        need(max(self.per_source,self.per_task,self.per_goal) <= self.max_batch <= self.max_operations <= self.resource_ceiling, 'QUOTA_CONSISTENCY')


@dataclass(frozen=True)
class SelectionRequest(Contract):
    request_id: str
    source_set_commitment: str
    requested_scope: tuple
    policy_commitment: str
    host_authorization_ref: str
    sequence: int
    commitment: str
    version: str = 'lrn002-v1'

    def validate(self):
        refs(self.requested_scope)
        ident(self.host_authorization_ref)
        integer(self.sequence)
        need(1 <= self.sequence <= 64, 'SEQUENCE')


@dataclass(frozen=True)
class EvidenceSelection(Contract):
    selection_id: str
    selected_refs: tuple
    excluded_refs: tuple
    exclusion_reasons: tuple
    source_commitments: tuple
    coverage: tuple
    commitment: str
    version: str = 'lrn002-v1'

    def validate(self):
        refs(self.selected_refs + self.excluded_refs)
        need(type(self.exclusion_reasons) is tuple and len(self.exclusion_reasons)==len(self.excluded_refs), 'REASONS')
        for reason in self.exclusion_reasons:
            ident(reason)
        need(type(self.source_commitments) is tuple and len(self.source_commitments)==len(self.selected_refs)+len(self.excluded_refs), 'SOURCES')
        for h in self.source_commitments:
            hashcheck(h)
        need(type(self.coverage) is tuple and len(self.coverage)==7, 'COVERAGE')
        for value in self.coverage[:5]:
            integer(value)
        need(self.coverage[0]==self.coverage[1]+self.coverage[2], 'COVERAGE_TOTAL')


@dataclass(frozen=True)
class ReplayBatch(Contract):
    batch_id: str
    ordered_experience_refs: tuple
    sequence_start: int
    sequence_end: int
    source_set_commitment: str
    selection_commitment: str
    commitment: str
    version: str = 'lrn002-v1'

    def validate(self):
        refs(self.ordered_experience_refs)
        integer(self.sequence_start)
        integer(self.sequence_end)
        need(self.sequence_end-self.sequence_start==len(self.ordered_experience_refs), 'BOUNDARIES')


@dataclass(frozen=True)
class ReplayObservation(Contract):
    observation_id: str
    batch_id: str
    replay_position: int
    observed_source_status: str
    verification_status: str
    source_eligibility: str
    commitment: str
    version: str = 'lrn002-v1'

    def validate(self):
        integer(self.replay_position)
        need(self.observed_source_status in learning.OUTCOMES, 'OUTCOME')
        need(self.verification_status in learning.CLASSES and self.verification_status!='VERIFIED_LOCAL', 'TRUST')
        need(self.source_eligibility in learning.ELIGIBILITY, 'ELIGIBILITY')


@dataclass(frozen=True)
class ReplayState(Contract):
    processed_request_ids: tuple
    replayed_batch_ids: tuple
    consumed: int
    remaining: int
    replay_operations: int
    previous_state_commitment: str
    policy_commitment: str
    replayed_sources: tuple
    history: tuple
    commitment: str
    version: str = 'lrn002-v1'

    def validate(self):
        refs(self.processed_request_ids)
        refs(self.replayed_batch_ids)
        refs(self.replayed_sources)
        for value in (self.consumed,self.remaining,self.replay_operations):
            integer(value)
        need(type(self.history) is tuple and len(self.history)==len(self.processed_request_ids)==len(self.replayed_batch_ids), 'HISTORY')
        need(self.replay_operations==len(self.replayed_sources), 'OPERATIONS')


@dataclass(frozen=True)
class ReplayVerdict(Contract):
    selection_status: str
    replay_status: str
    evidence_qualification: str
    blocking_findings: tuple
    commitment: str
    learning_authorized: bool = False
    model_update_authorized: bool = False
    knowledge_promotion_authorized: bool = False
    production_authorized: bool = False
    version: str = 'lrn002-v1'

    def validate(self):
        need(self.selection_status in ('SELECTED_FOR_DIAGNOSTIC_REPLAY','EXCLUDED'), 'STATUS')
        need(self.replay_status in ('DIAGNOSTIC_REPLAY_ONLY','EMPTY'), 'STATUS')
        need(self.evidence_qualification=='REQUIRES_VERIFICATION', 'TRUST')
        need(self.blocking_findings==BLOCKERS, 'FINDINGS')
        need(all(v is False for v in (self.learning_authorized,self.model_update_authorized,
             self.knowledge_promotion_authorized,self.production_authorized)), 'AUTHORITY')
