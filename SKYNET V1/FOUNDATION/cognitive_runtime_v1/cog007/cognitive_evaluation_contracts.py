"""Immutable benchmark contracts. Rates are explicit integer fractions."""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal
from cognitive_contracts import DTO,ResourcesV1,canonical_bytes,require,_decode,ContractError
Scenario = Literal['SUCCESS','REPLAY','TASK_REVISION','PLAN_REVISION','MISSING_BINDING','NONREADY','UNSUPPORTED','TOOL_BUDGET','STEP_BUDGET','INVALID_TOKENS','INVALID_TIME','TAMPER_EVIDENCE','REJECT_VERIFICATION','NO_COMPLETION','NO_PERSISTENCE','STABLE_FAILURE']

@dataclass(frozen=True)
class EvaluationCaseV1(DTO):
    schema_version: Literal['cog-evaluation-case-v1']
    case_id: str
    scenario: Scenario
    fixture_ref: Literal['COG006_FIXED_ABC_V1']
    expected_outcome: Literal['ISOLATED_CYCLE_SUCCEEDED','CYCLE_REJECTED','CYCLE_BUDGET_EXHAUSTED','CYCLE_DEPENDENCY_UNAVAILABLE','EVIDENCE_REJECTED']
    expected_reason: str
    expected_budget: ResourcesV1
    expected_production_authorized: Literal[False]
    expected_trusted_verification: Literal[False]
    expected_persisted: Literal[False]
    expected_trace: Literal['PRESENT_IDENTICAL','ABSENT']
    def __post_init__(self):
        super().__post_init__()
        require(re.fullmatch(r'cog007-[0-9]{3}',self.case_id) is not None,'CASE_ID')

@dataclass(frozen=True)
class EvaluationResultV1(DTO):
    schema_version: Literal['cog-evaluation-result-v1']
    case_id: str
    scenario: Scenario
    observed_outcome: str
    observed_reason: str
    observed_budget: ResourcesV1 | None
    trace_id: str | None
    outcome_correct: bool
    budget_correct: bool
    trust_violations: int
    trace_expected: bool
    trace_agrees: bool
    logical_agreement: bool
    input_unchanged: bool
    positive_semantics: bool
    unexpected_exception: bool
    passed: bool

@dataclass(frozen=True)
class RateV1(DTO):
    numerator: int
    denominator: int
    def __post_init__(self):
        super().__post_init__()
        require(self.numerator<=self.denominator,'RATE')

@dataclass(frozen=True)
class EvaluationSummaryV1(DTO):
    schema_version: Literal['cog-evaluation-summary-v1']
    results: tuple[EvaluationResultV1,...]
    total: int
    passed: int
    failed: int
    positive_success_rate: RateV1
    rejection_detection_rate: RateV1
    budget_accuracy: RateV1
    trace_agreement: RateV1
    logical_replay_agreement: RateV1
    trust_boundary_violations: int
    unexpected_exceptions: int
    def __post_init__(self):
        super().__post_init__()
        require(self.total==len(self.results)==self.passed+self.failed,'TOTAL')
        require(self.passed==sum(r.passed for r in self.results),'PASS_COUNT')
    @property
    def summary_id(self):
        return sha256(b'SKYNET:COGEvaluationSummaryV1:v1\0'+canonical_bytes(self)).hexdigest()

def parse_cases(raw: bytes) -> tuple[EvaluationCaseV1,...]:
    require(type(raw) is bytes and len(raw)<=100000,'CASE_BYTES')
    def pairs(items):
        d={}
        for k,v in items:
            require(k not in d,'DUPLICATE_KEY'); d[k]=v
        return d
    try:
        body=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs)
        require(type(body) is dict and set(body)=={'schema_version','cases'} and body['schema_version']=='cog-benchmark-cases-v1','CASE_SCHEMA')
        require(type(body['cases']) is list and 1<=len(body['cases'])<=64,'CASE_BOUND')
        cases=tuple(_decode(x,EvaluationCaseV1) for x in body['cases'])
        require(len({c.case_id for c in cases})==len(cases),'DUPLICATE_CASE')
        return cases
    except (UnicodeError,json.JSONDecodeError,TypeError,RecursionError):
        raise ContractError('MALFORMED_CASES') from None
