"""Host-supplied immutable orchestration contracts; no authority from hashes."""
from dataclasses import dataclass,fields
from agent_contracts import need,ident,integer,refs,hashcheck,plain,digest as base_digest

def digest(v):return base_digest('AGT002',v)
FINAL=('COMPLETED','PARTIAL','BLOCKED','STOPPED','DEADLINE','BUDGET_EXHAUSTED','FAILED')
STATES=('CREATED','VALIDATED','PLANNED','AUTHORIZED','RUNNING','EVALUATING')+FINAL
class Contract:
    def __post_init__(self):
        need(self.schema_version=='agt002-v1','VERSION');plain(self)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'):ident(v)
            if f.name.endswith('_commitment'):hashcheck(v)
        self.validate()
    def validate(self):pass
@dataclass(frozen=True)
class OrchestrationRequest(Contract):
    request_id:str;owner_id:str;task_ids:tuple;global_budget:int;max_tasks:int;max_depth:int;schema_version:str='agt002-v1'
    def validate(self):
        refs(self.task_ids);integer(self.global_budget);integer(self.max_tasks);integer(self.max_depth);need(1<=len(self.task_ids)<=self.max_tasks<=16 and 1<=self.max_depth<=8)
@dataclass(frozen=True)
class SupervisedAgent(Contract):
    agent_id:str;identity_commitment:str;allowed_task_ids:tuple;authorization_scope:str='LOCAL_DIAGNOSTIC';schema_version:str='agt002-v1'
    def validate(self):refs(self.allowed_task_ids);need(self.authorization_scope=='LOCAL_DIAGNOSTIC')
@dataclass(frozen=True)
class OrchestratedTask(Contract):
    task_id:str;agent_id:str;dependencies:tuple;task_commitment:str;grant_commitment:str;max_budget:int;schema_version:str='agt002-v1'
    def validate(self):refs(self.dependencies);need(self.task_id not in self.dependencies);integer(self.max_budget)
@dataclass(frozen=True)
class OrchestrationPlan(Contract):
    plan_id:str;request_id:str;ordered_task_ids:tuple;dependency_commitment:str;plan_commitment:str;schema_version:str='agt002-v1'
    def validate(self):refs(self.ordered_task_ids);need(self.plan_commitment==digest((self.request_id,self.ordered_task_ids,self.dependency_commitment)))
@dataclass(frozen=True)
class TaskExecutionRecord(Contract):
    task_id:str;agent_id:str;execution_status:str;trace_commitment:str;budget_consumed:int;dependency_status:str;reason_code:str;schema_version:str='agt002-v1'
    def validate(self):
        need(self.execution_status in FINAL+('REJECTED',));integer(self.budget_consumed);need(self.dependency_status in ('SATISFIED','BLOCKED','NOT_RUN'));ident(self.reason_code)
@dataclass(frozen=True)
class OrchestrationState(Contract):
    request_id:str;status:str;completed_tasks:tuple;failed_tasks:tuple;blocked_tasks:tuple;remaining_budget:int;transition_count:int;schema_version:str='agt002-v1'
    def validate(self):
        need(self.status in STATES)
        for r in (self.completed_tasks,self.failed_tasks,self.blocked_tasks):refs(r)
        refs(self.completed_tasks+self.failed_tasks+self.blocked_tasks);integer(self.remaining_budget);integer(self.transition_count)
@dataclass(frozen=True)
class OrchestrationTrace(Contract):
    trace_id:str;request_id:str;ordered_events:tuple;task_records:tuple;trace_commitment:str;binding_commitment:str;schema_version:str='agt002-v1'
    def validate(self):
        need(type(self.ordered_events) is tuple and type(self.task_records) is tuple and len(self.task_records)<=16)
        for r in self.task_records:need(type(r) is TaskExecutionRecord);r.__post_init__()
        refs(tuple(r.task_id for r in self.task_records));need(self.trace_commitment==digest((self.binding_commitment,self.ordered_events,self.task_records)));need(self.trace_id=='trace:'+self.trace_commitment)
@dataclass(frozen=True)
class OrchestrationVerdict(Contract):
    request_id:str;execution_status:str;completion_status:str;verification_status:str;reason_code:str;production_authorized:bool=False;knowledge_promotion_authorized:bool=False;schema_version:str='agt002-v1'
    def validate(self):
        need(self.execution_status in FINAL);need(self.completion_status==('LOCAL_COMPLETE' if self.execution_status=='COMPLETED' else 'INCOMPLETE'));need(self.verification_status=='NOT_ESTABLISHED');ident(self.reason_code);need(self.production_authorized is False and self.knowledge_promotion_authorized is False)
