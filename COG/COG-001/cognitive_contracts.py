"""Isolated COG-001 contracts; no operational SKYNET wire compatibility claimed."""
from __future__ import annotations
import hashlib
import json
import types
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from typing import Literal, get_args, get_origin, get_type_hints
from uuid import UUID

MAX = 2**63 - 1
Status = Literal['CREATED','VALIDATED','PLANNED','READY','RUNNING','VERIFYING','COMPLETED','FAILED','CANCELLED','BLOCKED']
TERMINAL = frozenset(('COMPLETED','FAILED','CANCELLED'))

class ContractError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)

def require(ok, code):
    if not ok:
        raise ContractError(code)

def identifier(value):
    try:
        require(type(value) is str and str(UUID(value)) == value and UUID(value).int != 0, 'IDENTIFIER')
    except (ValueError, AttributeError):
        raise ContractError('IDENTIFIER') from None

def timestamp(value):
    try:
        require(type(value) is str and len(value) == 27, 'TIMESTAMP')
        d = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
        require(d.strftime('%Y-%m-%dT%H:%M:%S.%fZ') == value, 'TIMESTAMP')
    except (ValueError, TypeError):
        raise ContractError('TIMESTAMP') from None

def digest_text(value):
    require(type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'DIGEST')

def _check(value, hint):
    origin, args = get_origin(hint), get_args(hint)
    if origin is Literal:
        require(any(type(value) is type(a) and value == a for a in args), 'ENUM')
    elif origin is types.UnionType:
        for a in args:
            try:
                _check(value, a)
                return
            except ContractError:
                pass
        raise ContractError('TYPE')
    elif origin is tuple:
        require(type(value) is tuple and len(value) <= 10000, 'TUPLE')
        for item in value:
            _check(item, args[0])
    elif hint is int:
        require(type(value) is int and 0 <= value <= MAX, 'INTEGER')
    elif hint is str:
        require(type(value) is str and 0 < len(value) <= 4096 and not any(ord(c)<32 or 0xD800<=ord(c)<=0xDFFF for c in value), 'TEXT')
    else:
        require(type(value) is hint, 'TYPE')
        if isinstance(value, DTO):
            value.__post_init__()

class DTO:
    def __post_init__(self):
        for name, hint in get_type_hints(type(self)).items():
            _check(getattr(self, name), hint)

def _plain(value):
    if is_dataclass(value):
        return {f.name: _plain(getattr(value, f.name)) for f in fields(value)}
    if type(value) is tuple:
        return [_plain(x) for x in value]
    return value

def canonical_bytes(value: DTO) -> bytes:
    require(isinstance(value, DTO), 'DTO')
    value.__post_init__()
    return json.dumps(_plain(value), sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')

def task_digest(task):
    return hashlib.sha256(b'SKYNET:COGTaskV1:v1\0' + canonical_bytes(task)).hexdigest()

def _decode(value, hint):
    origin, args = get_origin(hint), get_args(hint)
    if origin is types.UnionType:
        if value is None and type(None) in args:
            return None
        return _decode(value, next(a for a in args if a is not type(None)))
    if origin is tuple:
        require(type(value) is list, 'ARRAY')
        return tuple(_decode(x, args[0]) for x in value)
    if isinstance(hint, type) and issubclass(hint, DTO):
        require(type(value) is dict and set(value) == {f.name for f in fields(hint)}, 'FIELDS')
        hints = get_type_hints(hint)
        return hint(**{k: _decode(v, hints[k]) for k,v in value.items()})
    _check(value, hint)
    return value

def parse_dto(raw: bytes, cls):
    require(type(raw) is bytes and len(raw) <= 8_000_000 and cls in PUBLIC_DTOS, 'INPUT')
    def pairs(items):
        out = {}
        for k,v in items:
            require(k not in out, 'DUPLICATE_KEY')
            out[k] = v
        return out
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ContractError('NUMBER')))
        obj = _decode(value, cls)
        require(canonical_bytes(obj) == raw, 'NONCANONICAL')
        return obj
    except (UnicodeError, json.JSONDecodeError, RecursionError, TypeError) as exc:
        raise ContractError('MALFORMED') from exc

@dataclass(frozen=True)
class ResourcesV1(DTO):
    steps: int
    tool_calls: int
    model_calls: int
    tokens: int
    time_ms: int

@dataclass(frozen=True)
class TaskBudgetV1(DTO):
    schema_version: Literal['cog-budget-v1']
    maximum: ResourcesV1
    consumed: ResourcesV1
    def __post_init__(self):
        super().__post_init__()
        require(all(getattr(self.consumed,f.name)<=getattr(self.maximum,f.name) for f in fields(ResourcesV1)), 'BUDGET_TOTAL')

@dataclass(frozen=True)
class EvidenceRefV1(DTO):
    evidence_id: str
    content_hash: str
    provenance_id: str
    execution_id: str
    def __post_init__(self):
        super().__post_init__()
        for x in (self.evidence_id,self.provenance_id,self.execution_id): identifier(x)
        digest_text(self.content_hash)

@dataclass(frozen=True)
class TaskStepV1(DTO):
    schema_version: Literal['cog-step-v1']
    step_id: str
    description: str
    def __post_init__(self):
        super().__post_init__()
        identifier(self.step_id)

@dataclass(frozen=True)
class TaskResultV1(DTO):
    schema_version: Literal['cog-result-v1']
    content: str
    content_hash: str
    verification: Literal['UNVERIFIED','VERIFICATION_SIMULATED','VERIFICATION_TRUSTED']
    def __post_init__(self):
        super().__post_init__()
        require(self.content_hash == hashlib.sha256(self.content.encode('utf-8')).hexdigest(), 'RESULT_HASH')

@dataclass(frozen=True)
class CognitiveTaskV1(DTO):
    task_id: str
    schema_version: Literal['cog-task-v1']
    objective: str
    created_at: str
    priority: int
    status: Status
    revision: int
    budget: TaskBudgetV1
    steps: tuple[TaskStepV1,...]
    evidence_refs: tuple[EvidenceRefV1,...]
    result: TaskResultV1 | None
    failure_reason: str | None
    def __post_init__(self):
        super().__post_init__()
        identifier(self.task_id)
        timestamp(self.created_at)
        require(self.priority <= 100, 'PRIORITY')
        require(len({s.step_id for s in self.steps})==len(self.steps)==self.budget.consumed.steps, 'STEP_TOTAL')
        require(len({e.evidence_id for e in self.evidence_refs})==len(self.evidence_refs), 'EVIDENCE_DUPLICATE')
        require((self.failure_reason is not None)==(self.status in ('FAILED','CANCELLED','BLOCKED')), 'REASON')
        if self.result is not None:
            require(self.result.verification != 'VERIFICATION_TRUSTED', 'TRUST_BOUNDARY')
            require(self.status in ('VERIFYING','COMPLETED'), 'RESULT_STATE')
            if self.result.verification == 'VERIFICATION_SIMULATED':
                require(self.result.content == self.objective and any(e.content_hash==self.result.content_hash for e in self.evidence_refs), 'SIMULATION')
        if self.status=='COMPLETED':
            require(self.result is not None and self.result.verification=='VERIFICATION_SIMULATED', 'VERIFICATION_REQUIRED')

@dataclass(frozen=True)
class TaskTransitionV1(DTO):
    schema_version: Literal['cog-transition-v1']
    task_id: str
    expected_revision: int
    transition_type: Literal['VALIDATE','PLAN','READY','START','SUBMIT','VERIFY_SIMULATED','COMPLETE','FAIL','CANCEL','BLOCK','CONSUME']
    timestamp: str
    consumption: ResourcesV1 | None
    step: TaskStepV1 | None
    result: TaskResultV1 | None
    evidence_refs: tuple[EvidenceRefV1,...]
    reason: str | None
    def __post_init__(self):
        super().__post_init__()
        identifier(self.task_id)
        timestamp(self.timestamp)
        require((self.consumption is not None)==(self.transition_type=='CONSUME'), 'CONSUMPTION_FIELDS')
        require(self.step is None or self.transition_type=='CONSUME', 'STEP_FIELDS')
        require((self.result is not None)==(self.transition_type=='SUBMIT'), 'RESULT_FIELDS')
        require(not self.evidence_refs or self.transition_type=='SUBMIT', 'EVIDENCE_FIELDS')
        require((self.reason is not None)==(self.transition_type in ('FAIL','CANCEL','BLOCK')), 'REASON_FIELDS')

@dataclass(frozen=True)
class TaskEventV1(DTO):
    schema_version: Literal['cog-event-v1']
    task_id: str
    previous_revision: int
    new_revision: int
    previous_status: Status
    new_status: Status
    transition_type: str
    timestamp: str
    previous_task_digest: str
    new_task_digest: str
    previous_event_digest: str
    event_digest: str
    def __post_init__(self):
        super().__post_init__()
        identifier(self.task_id)
        timestamp(self.timestamp)
        require(self.new_revision==self.previous_revision+1, 'EVENT_REVISION')
        for x in (self.previous_task_digest,self.new_task_digest,self.previous_event_digest,self.event_digest): digest_text(x)

@dataclass(frozen=True)
class CognitiveStateV1(DTO):
    schema_version: Literal['cog-state-v1']
    task: CognitiveTaskV1
    events: tuple[TaskEventV1,...]
    def __post_init__(self):
        super().__post_init__()
        from cognitive_events import event_digest
        require(len(self.events)==self.task.revision, 'HISTORY_LENGTH')
        prev = '0'*64
        for i,e in enumerate(self.events):
            require(e.task_id==self.task.task_id and e.previous_revision==i and e.previous_event_digest==prev and event_digest(e)==e.event_digest, 'HISTORY')
            if i:
                require(e.previous_task_digest==self.events[i-1].new_task_digest and e.previous_status==self.events[i-1].new_status and e.timestamp>=self.events[i-1].timestamp, 'HISTORY_CHAIN')
            else:
                require(e.previous_status=='CREATED' and e.timestamp>=self.task.created_at, 'GENESIS')
            prev=e.event_digest
        if self.events:
            require(self.events[-1].new_task_digest==task_digest(self.task) and self.events[-1].new_status==self.task.status, 'HEAD')
        else:
            require(self.task.status=='CREATED' and self.task.result is None and not self.task.steps and all(getattr(self.task.budget.consumed,f.name)==0 for f in fields(ResourcesV1)), 'GENESIS')

PUBLIC_DTOS = (ResourcesV1,TaskBudgetV1,EvidenceRefV1,TaskStepV1,TaskResultV1,CognitiveTaskV1,TaskTransitionV1,TaskEventV1,CognitiveStateV1)
