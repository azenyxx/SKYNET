"""Synthetic provider boundary. Commitments authenticate no provider identity."""
from dataclasses import dataclass, asdict, fields
from hashlib import sha256
import json
import re
from cognitive_contracts import require, identifier, MAX
from cognitive_model_planning_contracts import ModelPlanningRequestV1
from cognitive_plan_contracts import PlanV1


def canonical(value):
    if hasattr(value, '__dataclass_fields__'): value=asdict(value)
    def plain(v):
        if hasattr(v, "__dataclass_fields__"): return plain(asdict(v))
        if type(v) is bytes: return {'hex':v.hex()}
        if type(v) is dict: return {k:plain(x) for k,x in v.items()}
        if type(v) in (list,tuple): return [plain(x) for x in v]
        return v
    return json.dumps(plain(value),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')

def commitment(domain,value): return sha256(('SKYNET:'+domain+':v1\0').encode()+canonical(value)).hexdigest()
def body(obj,excluded): return {f.name:getattr(obj,f.name) for f in fields(obj) if f.name!=excluded}
def label(x): require(type(x) is str and re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',x) is not None,'LABEL')
def number(x,positive=False): require(type(x) is int and (1 if positive else 0)<=x<=MAX,'NUMBER')

@dataclass(frozen=True)
class ProviderPolicyV1:
    allowed_provider_models: tuple[tuple[str,str],...]
    max_input_bytes: int
    max_output_bytes: int
    max_output_tokens: int
    max_latency_ms: int
    max_attempts: int=1
    def __post_init__(self):
        require(type(self.allowed_provider_models) is tuple and 1<=len(self.allowed_provider_models)<=64,'POLICY')
        for pair in self.allowed_provider_models:
            require(type(pair) is tuple and len(pair)==2,'POLICY'); label(pair[0]); label(pair[1])
        for n in ('max_input_bytes','max_output_bytes','max_output_tokens','max_latency_ms','max_attempts'): number(getattr(self,n),True)
        require(self.max_input_bytes<=65536 and self.max_output_bytes<=65536 and self.max_attempts==1,'V1_LIMIT')

@dataclass(frozen=True)
class ProviderRequestV1:
    request_id: str
    planning_request: ModelPlanningRequestV1
    provider_id: str
    model_id: str
    max_input_bytes: int
    max_output_bytes: int
    max_output_tokens: int
    max_latency_ms: int
    max_attempts: int=1
    request_commitment: str=''
    def __post_init__(self):
        identifier(self.request_id); label(self.provider_id); label(self.model_id)
        require(type(self.planning_request) is ModelPlanningRequestV1,'PLANNING_REQUEST'); self.planning_request.__post_init__()
        for n in ('max_input_bytes','max_output_bytes','max_output_tokens','max_latency_ms','max_attempts'): number(getattr(self,n),True)
        require(self.max_input_bytes<=65536 and self.max_output_bytes<=65536 and self.max_attempts==1,'V1_LIMIT')
        require(self.request_commitment==commitment('COGProviderRequestV1',body(self,'request_commitment')),'REQUEST_COMMITMENT')

@dataclass(frozen=True)
class ProviderResponseV1:
    request_id: str
    provider_id: str
    model_id: str
    raw_output: bytes
    reported_output_tokens: int
    reported_latency_ms: int
    finish_reason: str
    response_commitment: str
    def __post_init__(self):
        identifier(self.request_id); label(self.provider_id); label(self.model_id)
        require(type(self.raw_output) is bytes and len(self.raw_output)<=65536,'OUTPUT_BYTES')
        number(self.reported_output_tokens); number(self.reported_latency_ms)
        require(type(self.finish_reason) is str and self.finish_reason=='STOP','FINISH_REASON')
        require(self.response_commitment==commitment('COGProviderResponseV1',body(self,'response_commitment')),'RESPONSE_COMMITMENT')

@dataclass(frozen=True)
class ProviderInvocationResultV1:
    status: str
    reason_code: str
    validated_plan: PlanV1 | None
    provider_response_commitment: str | None
    planning_validation_commitment: str | None
    attempts_used: int
    reported_usage: tuple[int,int] | None
    trace_commitment: str
    @property
    def production_authorized(self): return False
    @property
    def executable(self): return False
    @property
    def trusted_verification(self): return False
