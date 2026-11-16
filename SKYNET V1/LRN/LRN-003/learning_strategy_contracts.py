"""Versioned advisory strategy DTOs. No execution or training authority."""
from dataclasses import dataclass, fields
import experience_replay as replay
from learning_contracts import need, ident, integer, refs, hashcheck

CATEGORIES = ('REPLAY_REWEIGHTING', 'EVIDENCE_FILTERING', 'EVALUATION_SCHEDULING')
BLOCKERS = replay.BLOCKERS + ('L02-001', 'L02-002', 'L02-003')


def digest(value):
    return replay.learning.memory.digest('LRN003', value)


def make(cls, **values):
    body = tuple((f.name, values.get(f.name, f.default)) for f in fields(cls) if f.name != 'commitment')
    return cls(**values, commitment=digest((cls.__name__, body)))


class Contract:
    def __post_init__(self):
        need(self.version == 'lrn003-v1', 'VERSION')
        replay.learning.memory.encoded(self)
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name.endswith('_id'):
                ident(value)
            if f.name.endswith('_commitment'):
                hashcheck(value)
        self.validate()
        body = tuple((f.name, getattr(self, f.name)) for f in fields(self) if f.name != 'commitment')
        need(self.commitment == digest((type(self).__name__, body)), 'COMMITMENT')


@dataclass(frozen=True)
class StrategyCandidate(Contract):
    strategy_id: str
    category: str
    estimated_cost: int
    uncertainty: str
    commitment: str
    version: str = 'lrn003-v1'

    def validate(self):
        need(self.category in CATEGORIES, 'CATEGORY')
        integer(self.estimated_cost)
        need(1 <= self.estimated_cost <= 64, 'COST')
        need(self.uncertainty == 'NOT_ESTABLISHED', 'UNCERTAINTY')


@dataclass(frozen=True)
class StrategyPolicy(Contract):
    policy_id: str
    categories: tuple
    resource_ceiling: int
    max_estimated_cost: int
    commitment: str
    version: str = 'lrn003-v1'

    def validate(self):
        refs(self.categories)
        need(set(self.categories) <= set(CATEGORIES), 'CATEGORY')
        integer(self.resource_ceiling)
        integer(self.max_estimated_cost)
        need(1 <= self.resource_ceiling <= 64 and 1 <= self.max_estimated_cost <= 64, 'LIMIT')


@dataclass(frozen=True)
class StrategyEvidence(Contract):
    evidence_id: str
    replay_commitment: str
    classifications: tuple
    outcomes: tuple
    source_commitments: tuple
    source_diversity: int
    commitment: str
    version: str = 'lrn003-v1'

    def validate(self):
        need(type(self.classifications) is tuple and len(self.classifications) <= 32, 'CLASSIFICATIONS')
        need(all(x in replay.learning.CLASSES and x != 'VERIFIED_LOCAL' for x in self.classifications), 'TRUST')
        need(type(self.outcomes) is tuple and len(self.outcomes) == len(self.classifications), 'OUTCOMES')
        need(all(x in replay.learning.OUTCOMES for x in self.outcomes), 'OUTCOME')
        need(type(self.source_commitments) is tuple and len(self.source_commitments) <= 32, 'SOURCES')
        for h in self.source_commitments:
            hashcheck(h)
        integer(self.source_diversity)
        need(self.source_diversity <= len(self.source_commitments), 'DIVERSITY')


@dataclass(frozen=True)
class StrategyEvaluation(Contract):
    strategy_id: str
    evidence_commitment: str
    status: str
    rationale: tuple
    estimated_cost: int
    commitment: str
    version: str = 'lrn003-v1'

    def validate(self):
        need(self.status in ('REQUIRES_MORE_EVIDENCE', 'REJECTED', 'BLOCKED', 'NOT_QUALIFIED', 'CANDIDATE_FOR_VALIDATION'), 'STATUS')
        refs(self.rationale)
        integer(self.estimated_cost)


@dataclass(frozen=True)
class StrategyComparison(Contract):
    ordered_strategy_ids: tuple
    basis: str
    commitment: str
    version: str = 'lrn003-v1'

    def validate(self):
        refs(self.ordered_strategy_ids)
        need(self.basis == 'ESTIMATED_COST_THEN_ID_NO_GAIN_CLAIM', 'BASIS')


@dataclass(frozen=True)
class AdaptationProposal(Contract):
    strategy_id: str
    supporting_evidence: tuple
    status: str
    rationale: tuple
    estimated_cost: int
    confidence_limitations: str
    required_validation: tuple
    blocking_findings: tuple
    commitment: str
    version: str = 'lrn003-v1'

    def validate(self):
        refs(self.supporting_evidence)
        refs(self.rationale)
        integer(self.estimated_cost)
        need(self.status in ('REQUIRES_MORE_EVIDENCE', 'REJECTED', 'BLOCKED', 'NOT_QUALIFIED', 'CANDIDATE_FOR_VALIDATION'), 'STATUS')
        need(self.confidence_limitations == 'NO_MEASURED_GAIN_OR_INDEPENDENT_PROVENANCE', 'CONFIDENCE')
        need(self.required_validation == ('INDEPENDENT_EVIDENCE', 'SEPARATE_AUTHORIZATION'), 'AUTHORITY')
        need(self.blocking_findings == BLOCKERS, 'FINDINGS')


@dataclass(frozen=True)
class StrategyState(Contract):
    processed_ids: tuple
    consumed: int
    remaining: int
    previous_state_commitment: str
    policy_commitment: str
    sequence: int
    history: tuple
    commitment: str
    version: str = 'lrn003-v1'

    def validate(self):
        refs(self.processed_ids)
        for value in (self.consumed, self.remaining, self.sequence):
            integer(value)
        need(self.consumed == len(self.processed_ids), 'ACCOUNTING')
        need(type(self.history) is tuple and len(self.history) == self.sequence <= self.consumed, 'HISTORY')


@dataclass(frozen=True)
class StrategyVerdict(Contract):
    status: str
    commitment: str
    learning_authorized: bool = False
    model_update_authorized: bool = False
    knowledge_promotion_authorized: bool = False
    production_authorized: bool = False
    version: str = 'lrn003-v1'

    def validate(self):
        need(self.status == 'ADVISORY_ONLY', 'STATUS')
        need(all(x is False for x in (self.learning_authorized, self.model_update_authorized,
             self.knowledge_promotion_authorized, self.production_authorized)), 'AUTHORITY')
