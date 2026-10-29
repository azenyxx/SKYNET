"""AGT-001 immutable local contracts. Hashes are integrity, not authority."""
from dataclasses import dataclass, fields, is_dataclass
from fractions import Fraction
import hashlib, json, re

OPS=('READ_CONTEXT','TRANSFORM','EVALUATE','RECORD')
TERMINAL=('COMPLETED','REJECTED','BLOCKED','STOPPED','DEADLINE','BUDGET_EXHAUSTED','FAILED')
STATUSES=('CREATED','VALIDATED','PLANNED','AUTHORIZED','EXECUTING','OBSERVING','EVALUATING')+TERMINAL
class Invalid(ValueError): pass
def need(ok,code='INVALID'):
    if not ok: raise Invalid(code)
def ident(x): need(type(x) is str and re.fullmatch(r'[A-Za-z0-9_.:-]{1,96}',x) is not None)
def integer(x): need(type(x) is int and 0<=x<=1000000)
def refs(x):
    need(type(x) is tuple and len(x)<=64)
    for y in x: ident(y)
    need(len(set(x))==len(x),'DUPLICATE')
def hashcheck(x): need(type(x) is str and re.fullmatch('[0-9a-f]{64}',x) is not None)
def plain(v,depth=0):
    need(depth<=16,'DEPTH')
    if is_dataclass(v): return {f.name:plain(getattr(v,f.name),depth+1) for f in fields(v)}
    if type(v) is Fraction:
        need(abs(v.numerator)<=10**12 and v.denominator<=10**12)
        return {'rational':[v.numerator,v.denominator]}
    if type(v) is dict:
        need(len(v)<=64 and all(type(k) is str for k in v))
        return {k:plain(x,depth+1) for k,x in v.items()}
    if type(v) is tuple:
        need(len(v)<=256);return [plain(x,depth+1) for x in v]
    if type(v) is str: need(len(v.encode('utf-8'))<=4096);return v
    if type(v) in (int,bool) or v is None:
        if type(v) is int: need(abs(v)<=10**12)
        return v
    raise Invalid('UNSUPPORTED_VALUE')
def digest(domain,v):
    return hashlib.sha256(('SKYNET:AGT001:'+domain+':v1\0').encode()+json.dumps(plain(v),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
class Contract:
    def __post_init__(self):
        need(self.schema_version=='agt001-v1','VERSION');plain(self)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id') and v!='': ident(v)
            if f.name.endswith('_commitment'): hashcheck(v)
        self.validate()
    def validate(self): pass
@dataclass(frozen=True)
class AgentIdentity(Contract):
    agent_id:str; agent_type:str; capability_ids:tuple; authority_scope:str='LOCAL_DIAGNOSTIC'; production_authorized:bool=False; schema_version:str='agt001-v1'
    def validate(self):
        ident(self.agent_type);refs(self.capability_ids);need(set(self.capability_ids)<=set(OPS));need(self.authority_scope=='LOCAL_DIAGNOSTIC' and self.production_authorized is False)
@dataclass(frozen=True)
class AgentTask(Contract):
    task_id:str; agent_id:str; objective:str; input_commitment:str; authorization_id:str; allowed_actions:tuple; max_actions:int; max_depth:int; max_budget:int; deadline:int; schema_version:str='agt001-v1'
    def validate(self):
        need(type(self.objective) is str and 0<len(self.objective)<=1024);refs(self.allowed_actions);need(set(self.allowed_actions)<=set(OPS))
        for v in (self.max_actions,self.max_depth,self.max_budget,self.deadline):integer(v)
        need(1<=self.max_actions<=64 and 1<=self.max_depth<=64)
@dataclass(frozen=True)
class AgentAction(Contract):
    action_id:str; task_id:str; action_type:str; input_payload:tuple; dependencies:tuple; estimated_cost:int; required_capability:str; schema_version:str='agt001-v1'
    def validate(self):
        need(self.action_type in OPS and self.required_capability==self.action_type);refs(self.dependencies);integer(self.estimated_cost);need(self.estimated_cost==1,'COST');need(type(self.input_payload) is tuple and len(self.input_payload)==2 and all(type(x) is str for x in self.input_payload));plain(self.input_payload)
@dataclass(frozen=True)
class AgentPlan(Contract):
    plan_id:str; task_id:str; actions:tuple; plan_commitment:str; status:str='VALIDATED'; schema_version:str='agt001-v1'
    def validate(self):
        need(self.status=='VALIDATED' and type(self.actions) is tuple and 0<len(self.actions)<=64)
        for a in self.actions:need(type(a) is AgentAction and a.task_id==self.task_id);a.__post_init__()
        refs(tuple(a.action_id for a in self.actions))
        need(self.plan_commitment==digest('plan',(self.task_id,self.actions)))
@dataclass(frozen=True)
class AgentObservation(Contract):
    observation_id:str; action_id:str; execution_status:str; input_commitment:str; output_commitment:str; evidence_refs:tuple; actual_cost:int; reason_code:str; schema_version:str='agt001-v1'
    def validate(self):
        need(self.execution_status in ('SUCCESS','FAILED'));integer(self.actual_cost);need(self.actual_cost==1);need(self.reason_code in ('DIAGNOSTIC','HANDLER_FAILED'));need(self.evidence_refs==(self.observation_id,),'EVIDENCE_BINDING')
@dataclass(frozen=True)
class AgentState(Contract):
    task_id:str; current_status:str; completed_actions:tuple; remaining_budget:int; last_observation_id:str; transition_count:int; schema_version:str='agt001-v1'
    def validate(self):
        need(self.current_status in STATUSES);refs(self.completed_actions);integer(self.remaining_budget);integer(self.transition_count)
@dataclass(frozen=True)
class AgentExecutionTrace(Contract):
    trace_id:str; task_id:str; ordered_events:tuple; observations:tuple; trace_commitment:str; replay_status:str='LOCAL_DIAGNOSTIC'; schema_version:str='agt001-v1'
    def validate(self):
        need(self.replay_status=='LOCAL_DIAGNOSTIC');need(type(self.observations) is tuple and len(self.observations)<=64)
        for o in self.observations:need(type(o) is AgentObservation);o.__post_init__()
        refs(tuple(o.observation_id for o in self.observations));need(self.trace_commitment==digest('trace',(self.task_id,self.ordered_events,self.observations)))
@dataclass(frozen=True)
class AgentVerdict(Contract):
    task_id:str; execution_status:str; completion_status:str; verification_status:str; reason_code:str; production_authorized:bool=False; knowledge_promotion_authorized:bool=False; schema_version:str='agt001-v1'
    def validate(self):
        need(self.execution_status in TERMINAL);need(self.completion_status==('LOCAL_COMPLETE' if self.execution_status=='COMPLETED' else 'INCOMPLETE'));need(self.verification_status=='NOT_ESTABLISHED');ident(self.reason_code);need(self.production_authorized is False and self.knowledge_promotion_authorized is False)
@dataclass(frozen=True)
class AuthorizationGrant(Contract):
    authorization_id:str; task_id:str; agent_id:str; task_commitment:str; candidate_commitment:str; max_budget:int; schema_version:str='agt001-v1'
    def validate(self):integer(self.max_budget)
