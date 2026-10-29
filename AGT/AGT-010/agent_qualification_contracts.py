"""Bounded local qualification records. Hashes do not establish authenticity."""
from dataclasses import dataclass, fields
import hashlib
import json
import re

STATUSES = ('QUALIFIED_LOCAL', 'QUALIFIED_PARTIAL', 'BLOCKED', 'FAILED',
            'NOT_TESTED', 'EVIDENCE_UNAVAILABLE', 'NOT_ESTABLISHED')
KINDS = ('REPORTED', 'CAPTURED_LOG', 'REPRODUCED', 'STATIC', 'INTEGRATION', 'INDEPENDENT')


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def plain(value):
    if hasattr(value, '__dataclass_fields__'):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)}
    if type(value) is tuple:
        require(len(value) <= 256, 'BOUND')
        return [plain(item) for item in value]
    if type(value) is str:
        require(len(value.encode('utf-8')) <= 8192, 'SIZE')
        return value
    if type(value) is int:
        require(0 <= value <= 1000000, 'INTEGER')
        return value
    if type(value) is bool:
        return value
    raise ValueError('TYPE')


def digest(value):
    data = json.dumps(plain(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(b'SKYNET:AGT010:v1\0' + data).hexdigest()


def identifier(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9_.:-]{1,96}', value) is not None, 'IDENTIFIER')


def refs(value):
    require(type(value) is tuple and len(value) <= 256, 'REFS')
    for item in value:
        identifier(item)
    require(len(value) == len(set(value)), 'DUPLICATE')


def make(cls, **values):
    body = tuple((f.name, values.get(f.name, f.default)) for f in fields(cls) if f.name != 'commitment')
    return cls(**values, commitment=digest(body))


class Record:
    def __post_init__(self):
        require(self.version == 'agt010-v1', 'VERSION')
        plain(self)
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name.endswith('_id'):
                identifier(value)
        self.validate()
        require(self.commitment == digest(tuple((f.name, getattr(self, f.name)) for f in fields(self) if f.name != 'commitment')), 'COMMITMENT')


@dataclass(frozen=True)
class ComponentDescriptor(Record):
    component_id: str
    capabilities: tuple
    interfaces: tuple
    dependencies: tuple
    commitment: str
    version: str = 'agt010-v1'

    def validate(self):
        for value in (self.capabilities, self.interfaces, self.dependencies):
            refs(value)


@dataclass(frozen=True)
class QualificationEvidence(Record):
    evidence_id: str
    component_id: str
    evidence_type: str
    source_commitment: str
    observed_result: str
    verification_status: str
    commitment: str
    version: str = 'agt010-v1'

    def validate(self):
        require(self.evidence_type in KINDS, 'KIND')
        require(self.observed_result in ('PASS', 'FAIL', 'ERROR', 'UNAVAILABLE'), 'RESULT')
        require(self.verification_status == 'NOT_ESTABLISHED', 'AUTHENTICITY')
        require(type(self.source_commitment) is str and re.fullmatch('[0-9a-f]{64}', self.source_commitment) is not None, 'HASH')


@dataclass(frozen=True)
class CapabilityAssessment(Record):
    capability_id: str
    supporting_components: tuple
    required_evidence: tuple
    qualification_status: str
    blocking_findings: tuple
    commitment: str
    version: str = 'agt010-v1'

    def validate(self):
        for value in (self.supporting_components, self.required_evidence, self.blocking_findings):
            refs(value)
        require(self.qualification_status in STATUSES, 'STATUS')


@dataclass(frozen=True)
class IntegrationDependency(Record):
    source_id: str
    target_id: str
    required_interface: str
    qualification_requirement: str
    commitment: str
    version: str = 'agt010-v1'

    def validate(self):
        identifier(self.required_interface)
        require(self.qualification_requirement in STATUSES, 'STATUS')


@dataclass(frozen=True)
class FindingRecord(Record):
    finding_id: str
    severity: str
    affected_components: tuple
    description: str
    status: str
    supporting_evidence: tuple
    commitment: str
    version: str = 'agt010-v1'

    def validate(self):
        require(self.severity in ('P1', 'P2'), 'SEVERITY')
        require(self.status == 'OPEN', 'NO_CLOSURE_EVIDENCE')
        require(bool(self.description), 'DESCRIPTION')
        refs(self.affected_components)
        refs(self.supporting_evidence)


@dataclass(frozen=True)
class QualificationPolicy(Record):
    policy_id: str
    minimum_evidence: int
    permitted_verdicts: tuple
    resource_ceiling: int
    commitment: str
    version: str = 'agt010-v1'

    def validate(self):
        require(type(self.minimum_evidence) is int and 1 <= self.minimum_evidence <= 32, 'MINIMUM')
        require(type(self.resource_ceiling) is int and 1 <= self.resource_ceiling <= 256, 'CEILING')
        refs(self.permitted_verdicts)
        require(set(self.permitted_verdicts) <= set(STATUSES), 'STATUS')


@dataclass(frozen=True)
class QualificationState(Record):
    processed_evidence_ids: tuple
    assessed_capabilities: tuple
    unresolved_findings: tuple
    previous_state_commitment: str
    consumed: int
    remaining: int
    history: tuple
    commitment: str
    version: str = 'agt010-v1'

    def validate(self):
        for value in (self.processed_evidence_ids, self.assessed_capabilities, self.unresolved_findings):
            refs(value)
        require(type(self.consumed) is int and type(self.remaining) is int, 'INTEGER')
        require(self.consumed == len(self.processed_evidence_ids), 'ACCOUNTING')
        require(type(self.history) is tuple and len(self.history) <= self.consumed, 'HISTORY')
        require(re.fullmatch('[0-9a-f]{64}', self.previous_state_commitment) is not None, 'HASH')


@dataclass(frozen=True)
class QualificationVerdict(Record):
    component_statuses: tuple
    integration_status: str
    verification_status: str
    blocking_findings: tuple
    commitment: str
    production_authorized: bool = False
    knowledge_promotion_authorized: bool = False
    version: str = 'agt010-v1'

    def validate(self):
        require(type(self.component_statuses) is tuple, 'COMPONENTS')
        ids = []
        for pair in self.component_statuses:
            require(type(pair) is tuple and len(pair) == 2, 'PAIR')
            identifier(pair[0])
            require(pair[1] in STATUSES, 'STATUS')
            ids.append(pair[0])
        require(len(set(ids)) == len(ids), 'DUPLICATE')
        refs(self.blocking_findings)
        require(self.integration_status in STATUSES, 'STATUS')
        require(self.verification_status == 'NOT_ESTABLISHED', 'TRUST')
        require(self.production_authorized is False and self.knowledge_promotion_authorized is False, 'AUTHORITY')
