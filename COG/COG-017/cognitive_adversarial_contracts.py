"""Bounded structural verification contracts; no provenance authority is created."""
from dataclasses import dataclass, asdict
import hashlib
import json
import re

class ContractError(ValueError): pass

def require(ok, code):
    if not ok: raise ContractError(code)

def ident(v):
    require(type(v) is str and re.fullmatch(r'[A-Za-z0-9_.:-]{1,96}', v) is not None, 'IDENTIFIER')

def integer(v, low=0, high=10**9):
    require(type(v) is int and low <= v <= high, 'INTEGER')

def refs(v):
    require(type(v) is tuple and len(v)<=64 and len(set(v))==len(v), 'REFERENCES')
    for x in v: ident(x)

def commitment(value):
    return hashlib.sha256(b'SKYNET:COG017:v1\0'+json.dumps(asdict(value),sort_keys=True,separators=(',', ':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()

@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    subject: str
    value: int
    source: str
    dependencies: tuple
    observed_at: int
    expires_at: int
    superseded: bool
    def __post_init__(self):
        for x in (self.evidence_id,self.subject,self.source): ident(x)
        integer(self.value,-10**9); refs(self.dependencies)
        integer(self.observed_at); integer(self.expires_at)
        require(self.expires_at>=self.observed_at and type(self.superseded) is bool,'TEMPORAL')

@dataclass(frozen=True)
class VerificationTarget:
    target_id: str
    producer: str
    subject: str
    conclusion: int
    inference: str
    dependencies: tuple
    def __post_init__(self):
        for x in (self.target_id,self.producer,self.subject): ident(x)
        integer(self.conclusion,-10**9);refs(self.dependencies)
        require(self.inference in ('DIRECT','SUM'), 'INFERENCE')

@dataclass(frozen=True)
class VerificationRequest:
    request_id: str
    target: VerificationTarget
    evidence_refs: tuple
    policy_id: str
    max_checks: int
    now: int
    deadline: int
    stop: bool
    schema_version: str='cog017-v1'
    def __post_init__(self):
        ident(self.request_id);ident(self.policy_id)
        require(type(self.target) is VerificationTarget,'TARGET');self.target.__post_init__()
        refs(self.evidence_refs);integer(self.max_checks,1,10000)
        integer(self.now);integer(self.deadline)
        require(type(self.stop) is bool and self.schema_version=='cog017-v1','SCHEMA')

@dataclass(frozen=True)
class AdversarialChallenge:
    challenge_id: str
    category: str

@dataclass(frozen=True)
class VerificationFinding:
    challenge_id: str
    evidence_refs: tuple
    reason_code: str

@dataclass(frozen=True)
class VerificationVerdict:
    target_id: str
    status: str
    challenge_ids: tuple
    evidence_refs: tuple
    findings: tuple
    boundary_id: str
    checks_used: int
    request_commitment: str
    snapshot_commitment: str
    independence: str='NOT_ESTABLISHED'
    production_authorized: bool=False
    promotion_authorized: bool=False
    @property
    def verdict_id(self): return commitment(self)
