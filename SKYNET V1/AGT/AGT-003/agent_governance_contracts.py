"""AGT-003: local diagnostic contracts; host authority is an external trust boundary."""
from dataclasses import dataclass,fields
import agent_contracts as ac
from agent_contracts import need,ident,integer,refs,hashcheck,plain

def digest(v):return ac.digest('AGT003',v)
TERMINAL=('COMPLETED','PARTIAL','STOPPED','DEADLINE','BUDGET_EXHAUSTED','BLOCKED','FAILED')
class Contract:
    def __post_init__(self):
        need(self.schema_version=='agt003-v1','VERSION');plain(self)
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'):ident(v)
            if f.name.endswith('_commitment'):hashcheck(v)
        self.validate()
    def validate(self):pass
@dataclass(frozen=True)
class DelegationGrant(Contract):
    delegation_id:str;issuer_id:str;delegate_agent_id:str;parent_authorization_id:str;allowed_task_ids:tuple;allowed_capabilities:tuple;max_budget:int;delegation_depth:int;schema_version:str='agt003-v1'
    def validate(self):
        refs(self.allowed_task_ids);refs(self.allowed_capabilities);need(bool(self.allowed_task_ids));need(set(self.allowed_capabilities)<=set(ac.OPS));integer(self.max_budget);integer(self.delegation_depth);need(self.delegation_depth==1,'SUBDELEGATION_DISABLED');need(self.issuer_id!=self.delegate_agent_id,'SELF_AUTHORITY')
@dataclass(frozen=True)
class DelegatedTask(Contract):
    task_id:str;delegation_id:str;agent_id:str;task_commitment:str;dependencies:tuple;allocated_budget:int;schema_version:str='agt003-v1'
    def validate(self):refs(self.dependencies);need(self.task_id not in self.dependencies);integer(self.allocated_budget)
@dataclass(frozen=True)
class ExecutionPolicy(Contract):
    policy_id:str;failure_mode:str;max_tasks:int;max_depth:int;global_budget:int;retry_limit:int=0;schema_version:str='agt003-v1'
    def validate(self):
        need(self.failure_mode in ('FAIL_STOP','CONTINUE_INDEPENDENT'))
        for v in (self.max_tasks,self.max_depth,self.global_budget,self.retry_limit):integer(v)
        need(1<=self.max_tasks<=16 and 1<=self.max_depth<=8);need(self.retry_limit==0,'RETRY_DISABLED')
@dataclass(frozen=True)
class TaskOutcome(Contract):
    task_id:str;execution_status:str;verification_status:str;confirmed_consumption:int;reserved_budget:int;uncertain_consumption:int;trace_commitment:str;reason_code:str;semantic_status:str='NOT_RUN';schema_version:str='agt003-v1'
    def validate(self):
        need(self.execution_status in TERMINAL+('REJECTED','UNCERTAIN'));need(self.verification_status=='NOT_ESTABLISHED')
        for v in (self.confirmed_consumption,self.reserved_budget,self.uncertain_consumption):integer(v)
        ident(self.reason_code);need(self.reserved_budget==0);need(self.semantic_status in ('NOT_RUN','LOCAL_REEXECUTION_CHECK'))
        if self.execution_status=='UNCERTAIN':need(self.confirmed_consumption==0 and self.reason_code=='EXECUTION_OUTCOME_UNCERTAIN' and self.semantic_status=='NOT_RUN')
        else:need(self.uncertain_consumption==0)
@dataclass(frozen=True)
class DependencyDecision(Contract):
    task_id:str;dependency_status:str;eligible_to_run:bool;blocking_task_ids:tuple;reason_code:str;schema_version:str='agt003-v1'
    def validate(self):
        refs(self.blocking_task_ids);ident(self.reason_code);need(type(self.eligible_to_run) is bool);need(self.dependency_status in ('SATISFIED','BLOCKED','NOT_RUN'));need(self.eligible_to_run==(self.dependency_status=='SATISFIED'));need(not self.eligible_to_run or not self.blocking_task_ids)
@dataclass(frozen=True)
class GovernanceState(Contract):
    request_id:str;completed_tasks:tuple;failed_tasks:tuple;blocked_tasks:tuple;pending_tasks:tuple;confirmed_spend:int;reserved_capacity:int;uncertain_spend:int;remaining_available_budget:int;status:str;authorized_global_budget:int;schema_version:str='agt003-v1'
    def validate(self):
        groups=(self.completed_tasks,self.failed_tasks,self.blocked_tasks,self.pending_tasks)
        for r in groups:refs(r)
        refs(sum(groups,()));need(self.status in TERMINAL+('RUNNING',))
        for v in (self.confirmed_spend,self.reserved_capacity,self.uncertain_spend,self.remaining_available_budget,self.authorized_global_budget):integer(v)
        need(self.confirmed_spend+self.reserved_capacity+self.uncertain_spend+self.remaining_available_budget==self.authorized_global_budget,'CONSERVATION')
@dataclass(frozen=True)
class GovernanceTrace(Contract):
    trace_id:str;request_id:str;ordered_decisions:tuple;task_outcomes:tuple;trace_commitment:str;binding_commitment:str;accounting_events:tuple;schema_version:str='agt003-v1'
    def validate(self):
        for group,kind in ((self.ordered_decisions,DependencyDecision),(self.task_outcomes,TaskOutcome)):
            need(type(group) is tuple and len(group)<=16)
            for x in group:need(type(x) is kind);x.__post_init__()
            refs(tuple(x.task_id for x in group))
        need(tuple(x.task_id for x in self.ordered_decisions)==tuple(x.task_id for x in self.task_outcomes));need(type(self.accounting_events) is tuple and len(self.accounting_events)<=32)
        for event in self.accounting_events:
            need(type(event) is tuple and len(event)==6);ident(event[0]);need(event[1] in ('RESERVE','CONFIRM','UNCERTAIN'))
            for v in event[2:]:integer(v)
        need(self.trace_commitment==digest((self.binding_commitment,self.ordered_decisions,self.task_outcomes,self.accounting_events)));need(self.trace_id=='trace:'+self.trace_commitment)
@dataclass(frozen=True)
class GovernanceVerdict(Contract):
    request_id:str;execution_status:str;completion_status:str;verification_status:str;reason_code:str;production_authorized:bool=False;knowledge_promotion_authorized:bool=False;schema_version:str='agt003-v1'
    def validate(self):
        need(self.execution_status in TERMINAL);need(self.completion_status==('LOCAL_COMPLETE' if self.execution_status=='COMPLETED' else 'INCOMPLETE'));need(self.verification_status=='NOT_ESTABLISHED');ident(self.reason_code);need(self.production_authorized is False and self.knowledge_promotion_authorized is False)
@dataclass(frozen=True)
class HostAuthority(Contract):
    """Must be supplied by trusted host, never extracted from agent output.
    No cryptographic origin claim: arbitrary host Python code is outside threat model.
    """
    owner_id:str;request_id:str;policy_commitment:str;delegation_commitments:tuple;parent_authorizations:tuple;parent_capabilities:tuple;approved_agent_ids:tuple;schema_version:str='agt003-v1'
    def validate(self):
        refs(self.approved_agent_ids);refs(self.parent_capabilities);need(set(self.parent_capabilities)<=set(ac.OPS));need(type(self.delegation_commitments) is tuple and 1<=len(self.delegation_commitments)<=16)
        for x in self.delegation_commitments:hashcheck(x)
        need(len(set(self.delegation_commitments))==len(self.delegation_commitments));need(type(self.parent_authorizations) is tuple and 1<=len(self.parent_authorizations)<=16)
        for g in self.parent_authorizations:need(type(g) is ac.AuthorizationGrant);g.__post_init__()
        refs(tuple(g.authorization_id for g in self.parent_authorizations))
