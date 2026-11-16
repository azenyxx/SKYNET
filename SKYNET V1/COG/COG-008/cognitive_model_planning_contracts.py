"""Isolated proposal contracts; request policy is supplied by the caller, not authenticated here."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal
from cognitive_contracts import DTO, ResourcesV1, canonical_bytes, require, identifier, digest_text
from cognitive_plan_contracts import PlanV1

OPERATIONS = frozenset(('ANALYZE', 'CHECK_CONSTRAINTS', 'SYNTHESIZE'))

@dataclass(frozen=True)
class ModelPlanningRequestV1(DTO):
    task_id: str
    task_revision: int
    objective: str
    allowed_operations: tuple[str, ...]
    max_steps: int
    max_dependencies: int
    max_response_bytes: int
    budget: ResourcesV1
    schema_version: Literal['cog-model-request-v1']

    def __post_init__(self):
        super().__post_init__()
        identifier(self.task_id)
        require(len(self.objective.encode('utf-8')) <= 4096, 'OBJECTIVE_SIZE')
        require(0 < len(self.allowed_operations) <= 3 and len(set(self.allowed_operations)) == len(self.allowed_operations) and set(self.allowed_operations) <= OPERATIONS, 'ALLOWLIST')
        require(1 <= self.max_steps <= 64 and self.max_dependencies <= 64, 'LIMITS')
        require(1 <= self.max_response_bytes <= 65536, 'RESPONSE_LIMIT')

    @property
    def request_binding(self):
        return sha256(b'SKYNET:COGModelPlanningRequestV1:v1\0' + canonical_bytes(self)).hexdigest()

@dataclass(frozen=True)
class ModelPlanningResponseV1:
    raw_response: bytes
    provider_label: str
    request_binding: str

    def __post_init__(self):
        require(type(self.raw_response) is bytes and len(self.raw_response) <= 65536, 'RESPONSE_BYTES')
        require(type(self.provider_label) is str and 1 <= len(self.provider_label) <= 64 and self.provider_label.isascii() and all(32 <= ord(c) < 127 for c in self.provider_label), 'PROVIDER_LABEL')
        digest_text(self.request_binding)

@dataclass(frozen=True)
class ModelPlanValidationV1(DTO):
    status: Literal['MODEL_PLAN_ACCEPTED_ISOLATED', 'MODEL_PLAN_REJECTED']
    reason_code: str
    validated_plan: PlanV1 | None
    response_commitment: str
    request_binding: str

    def __post_init__(self):
        super().__post_init__()
        digest_text(self.response_commitment)
        digest_text(self.request_binding)
        require((self.status == 'MODEL_PLAN_ACCEPTED_ISOLATED') == (self.validated_plan is not None), 'RESULT_STATE')

    @property
    def executable(self): return False
    @property
    def production_authorized(self): return False
    @property
    def trusted_verification(self): return False
