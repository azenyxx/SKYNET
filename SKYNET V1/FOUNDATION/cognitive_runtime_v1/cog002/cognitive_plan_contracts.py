"""Pure advice contracts. COG-001 supplies strict scalar/resource validation."""
from __future__ import annotations
from dataclasses import dataclass, fields
from typing import Literal
from hashlib import sha256
from cognitive_contracts import DTO, ResourcesV1, MAX, canonical_bytes, require, digest_text, identifier

@dataclass(frozen=True)
class PlanStepV1(DTO):
    schema_version: Literal['cog-plan-step-v1']
    step_id: str
    operation: Literal['ANALYZE','CHECK_CONSTRAINTS','SYNTHESIZE']
    dependencies: tuple[str,...]
    estimate: ResourcesV1
    max_retries: int
    status: Literal['PENDING','COMPLETED','FAILED']
    attempts: int

    def __post_init__(self):
        super().__post_init__()
        identifier(self.step_id)
        require(len(self.dependencies)<=64 and len(set(self.dependencies))==len(self.dependencies),'DEPENDENCIES')
        for dep in self.dependencies: identifier(dep)
        require(self.max_retries<=3 and self.attempts<=self.max_retries+1,'RETRY_LIMIT')
        require(self.estimate.steps==1,'STEP_ESTIMATE')
        require((self.status=='PENDING' and self.attempts==0) or
                (self.status!='PENDING' and self.attempts>=1),'ATTEMPT_STATE')

def validate_graph(steps):
    ids={s.step_id for s in steps}
    require(len(ids)==len(steps),'DUPLICATE_STEP')
    require(all(set(s.dependencies)<=ids for s in steps),'MISSING_DEPENDENCY')
    remaining=set(ids)
    for _ in steps:
        ready={s.step_id for s in steps if s.step_id in remaining and not (set(s.dependencies)&remaining)}
        if not remaining: return
        require(bool(ready),'CYCLE')
        remaining-=ready
    require(not remaining,'CYCLE')

@dataclass(frozen=True)
class PlanV1(DTO):
    schema_version: Literal['cog-plan-v1']
    task_id: str
    task_revision: int
    task_commitment: str
    steps: tuple[PlanStepV1,...]

    def __post_init__(self):
        super().__post_init__()
        identifier(self.task_id)
        digest_text(self.task_commitment)
        require(1<=len(self.steps)<=64,'PLAN_BOUND')
        require(tuple(s.step_id for s in self.steps)==tuple(sorted(s.step_id for s in self.steps)),'STEP_ORDER')
        require(all(s.status=='PENDING' and s.attempts==0 for s in self.steps),'INITIAL_STEPS')
        validate_graph(self.steps)

    @property
    def plan_id(self):
        return sha256(b'SKYNET:COGPlanV1:v1\0'+canonical_bytes(self)).hexdigest()

    @property
    def executable(self): return False

@dataclass(frozen=True)
class PlanProgressV1(DTO):
    schema_version: Literal['cog-plan-progress-v1']
    plan_id: str
    revision: int
    steps: tuple[PlanStepV1,...]
    consumed_estimate: ResourcesV1
    outcome: Literal['ACTIVE','COMPLETED','FAILED']

    def __post_init__(self):
        super().__post_init__()
        digest_text(self.plan_id)
        require(1<=len(self.steps)<=64,'PLAN_BOUND')
        validate_graph(self.steps)
        require(self.revision==sum(s.attempts for s in self.steps),'PROGRESS_REVISION')
        for f in fields(ResourcesV1):
            total=sum(getattr(s.estimate,f.name)*s.attempts for s in self.steps)
            require(total<=MAX and total==getattr(self.consumed_estimate,f.name),'PROGRESS_TOTAL')
        by_id={s.step_id:s for s in self.steps}
        require(all(s.attempts==0 or all(by_id[d].status=='COMPLETED' for d in s.dependencies) for s in self.steps),'DEPENDENCY_PROGRESS')
        exhausted=any(s.status=='FAILED' and s.attempts==s.max_retries+1 for s in self.steps)
        expected='FAILED' if exhausted else ('COMPLETED' if all(s.status=='COMPLETED' for s in self.steps) else 'ACTIVE')
        require(self.outcome==expected,'OUTCOME')

    @property
    def executable(self): return False

@dataclass(frozen=True)
class PlanDecisionV1(DTO):
    schema_version: Literal['cog-plan-decision-v1']
    plan_id: str
    expected_revision: int
    step_id: str
    action: Literal['COMPLETE','FAIL','RETRY_COMPLETE','RETRY_FAIL']

    def __post_init__(self):
        super().__post_init__()
        digest_text(self.plan_id)
        identifier(self.step_id)

    @property
    def executable(self): return False
