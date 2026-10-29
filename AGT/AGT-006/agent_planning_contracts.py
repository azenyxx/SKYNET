"""AGT006 v1: exact host pins, diagnostic output, no independent authority."""
from dataclasses import dataclass,fields
import agent_memory_contracts as mc
from agent_contracts import need,ident,integer,hashcheck

def digest(value):return mc.digest('AGT006',value)
def refs(value,n=16):mc.refs(value,n)
def payload(obj):return tuple((f.name,getattr(obj,f.name)) for f in fields(obj) if f.name!=obj.HASH)
def make(cls,**kw):
    values=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!=cls.HASH)
    return cls(**kw,**{cls.HASH:digest(values)})
class Contract:
    HASH=''
    def __post_init__(self):
        need(self.schema_version=='agt006-v1','VERSION');mc.encoded(self)
        for f in fields(self):
            value=getattr(self,f.name)
            if f.name.endswith('_id'):ident(value)
            if f.name.endswith('_commitment'):hashcheck(value)
        self.validate()
        if self.HASH:need(getattr(self,self.HASH)==digest(payload(self)),'COMMITMENT')
    def validate(self):pass
@dataclass(frozen=True)
class AgentGoal(Contract):
    HASH='goal_commitment'
    goal_id:str;owner_agent_id:str;objective:str;success_criteria:tuple;constraints:tuple;authorized_capabilities:tuple;resource_budget:int;goal_commitment:str;schema_version:str='agt006-v1'
    def validate(self):
        need(type(self.objective) is str and 0<len(self.objective.encode('utf-8'))<=4096);need(self.success_criteria==('ALL_TASKS_COMPLETED',));need(self.constraints==('LOCAL_ONLY','NO_RETRY'));refs(self.authorized_capabilities,4);need(set(self.authorized_capabilities)<=set(('READ_CONTEXT','TRANSFORM','EVALUATE','RECORD')));integer(self.resource_budget)
@dataclass(frozen=True)
class GoalDecomposition(Contract):
    HASH='decomposition_commitment'
    decomposition_id:str;goal_id:str;subgoal_ids:tuple;dependency_edges:tuple;decomposition_commitment:str;schema_version:str='agt006-v1'
    def validate(self):refs(self.subgoal_ids);edges(self.dependency_edges,self.subgoal_ids)
def edges(value,ids):
    need(type(value) is tuple and len(value)<=120);need(len(set(value))==len(value))
    for e in value:need(type(e) is tuple and len(e)==2 and e[0] in ids and e[1] in ids and e[0]!=e[1])
@dataclass(frozen=True)
class PlanTask(Contract):
    HASH='task_commitment'
    task_id:str;goal_id:str;assigned_agent_id:str;required_capabilities:tuple;dependency_ids:tuple;estimated_cost:int;source_task_commitment:str;task_commitment:str;schema_version:str='agt006-v1'
    def validate(self):refs(self.required_capabilities,4);refs(self.dependency_ids);need(self.task_id not in self.dependency_ids);integer(self.estimated_cost)
@dataclass(frozen=True)
class ExecutionPlan(Contract):
    HASH='plan_commitment'
    plan_id:str;goal_id:str;ordered_tasks:tuple;dependency_edges:tuple;total_estimated_cost:int;plan_version:int;goal_commitment:str;source_commitment:str;plan_commitment:str;schema_version:str='agt006-v1'
    def validate(self):
        need(type(self.ordered_tasks) is tuple and 1<=len(self.ordered_tasks)<=16);seen=[];depth={}
        for t in self.ordered_tasks:
            need(type(t) is PlanTask);t.__post_init__();need(t.goal_id==self.goal_id and t.task_id not in seen);need(set(t.dependency_ids)<=set(seen),'ORDER');depth[t.task_id]=1+max((depth[x] for x in t.dependency_ids),default=0);need(depth[t.task_id]<=8);seen.append(t.task_id)
        need(len({t.assigned_agent_id for t in self.ordered_tasks})<=8);edges(self.dependency_edges,tuple(seen));need(self.dependency_edges==tuple((d,t.task_id) for t in self.ordered_tasks for d in t.dependency_ids));integer(self.total_estimated_cost);need(self.total_estimated_cost==sum(t.estimated_cost for t in self.ordered_tasks));integer(self.plan_version);need(self.plan_version<=4)
@dataclass(frozen=True)
class PlanEvaluation(Contract):
    HASH='evaluation_commitment'
    evaluation_id:str;plan_id:str;feasibility_status:str;constraint_violations:tuple;resource_projection:int;evaluation_commitment:str;schema_version:str='agt006-v1'
    def validate(self):need(self.feasibility_status in ('FEASIBLE','INFEASIBLE','BLOCKED_DEPENDENCY','INSUFFICIENT_AUTHORITY','INSUFFICIENT_BUDGET'));refs(self.constraint_violations);integer(self.resource_projection)
@dataclass(frozen=True)
class PlanRevision(Contract):
    HASH='revision_commitment'
    revision_id:str;previous_plan_commitment:str;new_plan_commitment:str;revision_reason:str;affected_task_ids:tuple;authorization_commitment:str;revision_commitment:str;schema_version:str='agt006-v1'
    def validate(self):need(self.revision_reason in ('FAILED_TASK','BLOCKED_DEPENDENCY','INSUFFICIENT_BUDGET','UNAVAILABLE_AGENT','CHANGED_CONSTRAINTS'));refs(self.affected_task_ids)
@dataclass(frozen=True)
class PlanningState(Contract):
    HASH='state_commitment'
    goal_id:str;active_plan_commitment:str;completed_task_ids:tuple;failed_task_ids:tuple;blocked_task_ids:tuple;consumed_budget:int;remaining_budget:int;revision_count:int;state_commitment:str;uncertain_consumption:int=0;reserved_consumption:int=0;executed:bool=False;outcome_commitment:str='0'*64;schema_version:str='agt006-v1'
    def validate(self):
        refs(self.completed_task_ids+self.failed_task_ids+self.blocked_task_ids)
        for value in (self.consumed_budget,self.remaining_budget,self.revision_count,self.uncertain_consumption,self.reserved_consumption):integer(value)
        need(self.revision_count<=4 and type(self.executed) is bool);need(self.reserved_consumption==0)
@dataclass(frozen=True)
class PlanningVerdict(Contract):
    goal_id:str;plan_id:str;execution_status:str;verification_status:str;reason_code:str;production_authorized:bool=False;knowledge_promotion_authorized:bool=False;schema_version:str='agt006-v1'
    def validate(self):need(self.execution_status in ('COMPLETED','PARTIAL','STOPPED','DEADLINE','BUDGET_EXHAUSTED','BLOCKED','FAILED'));need(self.verification_status=='NOT_ESTABLISHED');ident(self.reason_code);need(self.production_authorized is False and self.knowledge_promotion_authorized is False)
@dataclass(frozen=True)
class HostApproval:
    """Trusted local host input, never derived from agent output or memory."""
    goal_commitment:str;source_commitments:tuple;expected_state:str;execution_plans:tuple=();revision_approvals:tuple=();context_approvals:tuple=()
    def __post_init__(self):
        hashcheck(self.goal_commitment);hashcheck(self.expected_state)
        for values in (self.source_commitments,self.execution_plans,self.revision_approvals,self.context_approvals):
            need(type(values) is tuple and len(values)<=4 and len(set(values))==len(values))
            for x in values:hashcheck(x)
