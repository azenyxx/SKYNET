"""Local diagnostic learning evidence; no training or knowledge authority."""
from dataclasses import dataclass, fields
import hashlib
import json
import re

CLASSES = ('VERIFIED_LOCAL', 'REPORTED_ONLY', 'PARTIALLY_VERIFIED',
           'CONTRADICTED', 'UNAVAILABLE', 'NOT_ESTABLISHED')
ELIGIBILITY = ('ELIGIBLE_FOR_EVALUATION', 'REQUIRES_VERIFICATION', 'REJECTED',
               'BLOCKED', 'NOT_QUALIFIED')
OUTCOMES = ('COMPLETED', 'FAILED', 'BLOCKED', 'UNCERTAIN', 'STOPPED',
            'DEADLINE', 'BUDGET_EXHAUSTED', 'UNKNOWN')


def need(condition, code):
    if not condition:
        raise ValueError(code)


def ident(value):
    need(type(value) is str and re.fullmatch(r'[A-Za-z0-9_.:-]{1,96}', value) is not None, 'IDENTIFIER')


def integer(value):
    need(type(value) is int and 0 <= value <= 1000000, 'INTEGER')


def hashcheck(value):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'HASH')


def refs(value):
    need(type(value) is tuple and len(value) <= 64, 'REFS')
    for item in value:
        ident(item)
    need(len(set(value)) == len(value), 'DUPLICATE')


def plain(value):
    if hasattr(value, '__dataclass_fields__'):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)}
    if type(value) is tuple:
        need(len(value) <= 64, 'COLLECTION_LIMIT')
        return [plain(x) for x in value]
    if type(value) is str:
        need(len(value.encode('utf-8')) <= 4096, 'TEXT_LIMIT')
        return value
    if type(value) is bool:
        return value
    if type(value) is int:
        integer(value)
        return value
    raise ValueError('TYPE')


def digest(value):
    data = json.dumps(plain(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(b'SKYNET:LRN001:v1\0' + data).hexdigest()


def make(cls, **values):
    body = tuple((f.name, values.get(f.name, f.default)) for f in fields(cls) if f.name != 'commitment')
    return cls(**values, commitment=digest(body))


class Contract:
    def __post_init__(self):
        need(self.version == 'lrn001-v1', 'VERSION')
        plain(self)
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
class ExperienceRecord(Contract):
    experience_id: str
    agent_id: str
    task_id: str
    goal_id: str
    workflow_id: str
    sequence: int
    action_category: str
    reported_outcome: str
    source_evidence_commitment: str
    commitment: str
    version: str = 'lrn001-v1'

    def validate(self):
        integer(self.sequence)
        need(1 <= self.sequence <= 64, 'SEQUENCE')
        need(self.action_category == 'GOVERNANCE_DIAGNOSTIC', 'ACTION')
        need(self.reported_outcome in OUTCOMES, 'OUTCOME')


@dataclass(frozen=True)
class OutcomeEvidence(Contract):
    evidence_id: str
    experience_id: str
    observed_result: str
    verification_level: str
    provenance_ref: str
    confidence_metadata: tuple
    commitment: str
    version: str = 'lrn001-v1'

    def validate(self):
        need(self.observed_result in OUTCOMES, 'OUTCOME')
        need(self.verification_level in CLASSES, 'CLASS')
        if self.provenance_ref:
            ident(self.provenance_ref)
        need(type(self.confidence_metadata) is tuple and len(self.confidence_metadata) == 2, 'CONFIDENCE')
        numerator, denominator = self.confidence_metadata
        integer(numerator)
        integer(denominator)
        need(0 < denominator <= 10000 and numerator <= denominator, 'CONFIDENCE')


@dataclass(frozen=True)
class LearningSignal(Contract):
    signal_id: str
    experience_id: str
    feedback_category: str
    outcome_attribution: str
    signal_quality: str
    commitment: str
    version: str = 'lrn001-v1'

    def validate(self):
        need(self.feedback_category == 'DIAGNOSTIC_ONLY', 'FEEDBACK')
        need(self.outcome_attribution in OUTCOMES, 'ATTRIBUTION')
        need(self.signal_quality in CLASSES, 'CLASS')


@dataclass(frozen=True)
class LearningPolicy(Contract):
    policy_id: str
    allowed_evidence_classes: tuple
    minimum_verification: str
    max_processing_budget: int
    promotion_restrictions: tuple
    commitment: str
    version: str = 'lrn001-v1'

    def validate(self):
        refs(self.allowed_evidence_classes)
        need(set(self.allowed_evidence_classes) <= set(CLASSES), 'CLASS')
        need(self.minimum_verification == 'VERIFIED_LOCAL', 'MINIMUM')
        integer(self.max_processing_budget)
        need(1 <= self.max_processing_budget <= 64, 'BUDGET')
        need(self.promotion_restrictions == ('NO_TRAINING', 'NO_PROMOTION', 'NO_PRODUCTION'), 'AUTHORITY')


@dataclass(frozen=True)
class ExperienceAssessment(Contract):
    experience_id: str
    evidence_validity: str
    eligibility_status: str
    confidence_category: str
    rejection_reasons: tuple
    commitment: str
    version: str = 'lrn001-v1'

    def validate(self):
        need(self.evidence_validity in CLASSES, 'CLASS')
        need(self.eligibility_status in ELIGIBILITY, 'ELIGIBILITY')
        need(self.confidence_category == 'CALLER_REPORTED_UNCALIBRATED', 'CONFIDENCE')
        refs(self.rejection_reasons)


@dataclass(frozen=True)
class LearningCandidate(Contract):
    candidate_id: str
    supporting_experience_ids: tuple
    proposed_learning_objective: str
    required_validation: tuple
    commitment: str
    version: str = 'lrn001-v1'

    def validate(self):
        refs(self.supporting_experience_ids)
        need(bool(self.supporting_experience_ids), 'SUPPORT')
        need(self.proposed_learning_objective == 'DIAGNOSTIC_REVIEW_ONLY', 'OBJECTIVE')
        need(self.required_validation == ('INDEPENDENT_PROVENANCE', 'SEPARATE_LEARNING_AUTHORIZATION'), 'AUTHORITY')


@dataclass(frozen=True)
class LearningState(Contract):
    processed_experience_ids: tuple
    accepted_evidence_refs: tuple
    rejected_evidence_refs: tuple
    candidate_refs: tuple
    consumed: int
    remaining: int
    previous_state_commitment: str
    policy_commitment: str
    source_refs: tuple
    history: tuple
    commitment: str
    version: str = 'lrn001-v1'

    def validate(self):
        for value in (self.processed_experience_ids, self.accepted_evidence_refs,
                      self.rejected_evidence_refs, self.candidate_refs, self.source_refs):
            refs(value)
        refs(self.accepted_evidence_refs + self.rejected_evidence_refs)
        integer(self.consumed)
        integer(self.remaining)
        need(self.consumed == len(self.processed_experience_ids) == len(self.source_refs), 'ACCOUNTING')
        need(self.consumed == len(self.accepted_evidence_refs) + len(self.rejected_evidence_refs), 'EVIDENCE_COUNT')
        need(type(self.history) is tuple and len(self.history) == self.consumed, 'HISTORY')


@dataclass(frozen=True)
class LearningVerdict(Contract):
    processing_status: str
    evidence_qualification: str
    learning_eligibility: str
    reason_codes: tuple
    commitment: str
    knowledge_promotion_authorized: bool = False
    model_update_authorized: bool = False
    production_authorized: bool = False
    version: str = 'lrn001-v1'

    def validate(self):
        need(self.processing_status == 'RECORDED_DIAGNOSTIC', 'STATUS')
        need(self.evidence_qualification in CLASSES, 'CLASS')
        need(self.learning_eligibility in ELIGIBILITY, 'ELIGIBILITY')
        refs(self.reason_codes)
        need(self.knowledge_promotion_authorized is False and self.model_update_authorized is False
             and self.production_authorized is False, 'AUTHORITY')
