"""Local lifecycle records; host pins do not establish independent provenance."""
from dataclasses import dataclass, fields
import agent_recovery as recovery
from agent_contracts import need, ident, integer, hashcheck

STATUSES = ('CREATED', 'AUTHORIZED', 'READY', 'RUNNING', 'PAUSED', 'BLOCKED',
            'COMPLETED', 'FAILED', 'UNCERTAIN', 'TERMINATED')
TRANSITIONS = (('CREATED', 'AUTHORIZED'), ('AUTHORIZED', 'READY'),
               ('READY', 'RUNNING'), ('RUNNING', 'COMPLETED'),
               ('RUNNING', 'FAILED'), ('RUNNING', 'UNCERTAIN'),
               ('RUNNING', 'BLOCKED'), ('RUNNING', 'PAUSED'),
               ('PAUSED', 'READY'), ('BLOCKED', 'READY'),
               ('CREATED', 'TERMINATED'), ('READY', 'TERMINATED'))


def digest(value):
    return recovery.feedback.planning.mc.digest('AGT009', value)


def make(cls, **values):
    body = tuple((f.name, values.get(f.name, f.default))
                 for f in fields(cls) if f.name != cls.HASH)
    return cls(**values, **{cls.HASH: digest(body)})


class Contract:
    def __post_init__(self):
        need(self.schema_version == 'agt009-v1', 'VERSION')
        recovery.feedback.planning.mc.encoded(self)
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name.endswith('_id'):
                ident(value)
            if field.name.endswith('_commitment'):
                hashcheck(value)
        self.validate()
        body = tuple((f.name, getattr(self, f.name))
                     for f in fields(self) if f.name != self.HASH)
        need(getattr(self, self.HASH) == digest(body), 'COMMITMENT')


@dataclass(frozen=True)
class AgentLifecycle(Contract):
    HASH = 'lifecycle_commitment'
    agent_id: str
    status: str
    approved_capabilities: tuple
    current_task: str
    lifecycle_commitment: str
    schema_version: str = 'agt009-v1'

    def validate(self):
        need(self.status in STATUSES, 'STATUS')
        ident(self.current_task)
        recovery.refs(self.approved_capabilities, 4)
        need(set(self.approved_capabilities) <= set(recovery.feedback.planning.gov.ac.OPS), 'CAPABILITY')


@dataclass(frozen=True)
class WorkflowLifecycle(Contract):
    HASH = 'workflow_commitment'
    workflow_id: str
    goal_id: str
    plan_commitment: str
    task_statuses: tuple
    workflow_commitment: str
    schema_version: str = 'agt009-v1'

    def validate(self):
        need(type(self.task_statuses) is tuple and 0 < len(self.task_statuses) <= 16, 'TASKS')
        ids = []
        for pair in self.task_statuses:
            need(type(pair) is tuple and len(pair) == 2, 'TASK')
            ident(pair[0])
            need(pair[1] in STATUSES + ('STOPPED', 'DEADLINE', 'BUDGET_EXHAUSTED'), 'STATUS')
            ids.append(pair[0])
        need(len(set(ids)) == len(ids), 'DUPLICATE')


@dataclass(frozen=True)
class SupervisionPolicy(Contract):
    HASH = 'policy_commitment'
    policy_id: str
    allowed_transitions: tuple
    resource_ceiling: int
    stop_rules: str
    policy_commitment: str
    schema_version: str = 'agt009-v1'

    def validate(self):
        need(type(self.allowed_transitions) is tuple and len(self.allowed_transitions) <= 12, 'TRANSITIONS')
        need(all(type(x) is tuple and x in TRANSITIONS for x in self.allowed_transitions), 'TRANSITION')
        need(len(set(self.allowed_transitions)) == len(self.allowed_transitions), 'DUPLICATE')
        integer(self.resource_ceiling)
        need(self.stop_rules == 'REJECT_ALL', 'STOP_POLICY')


@dataclass(frozen=True)
class TransitionRequest(Contract):
    HASH = 'request_commitment'
    request_id: str
    source_status: str
    target_status: str
    actor_id: str
    reason: str
    source_state_commitment: str
    request_commitment: str
    schema_version: str = 'agt009-v1'

    def validate(self):
        need(self.source_status in STATUSES and self.target_status in STATUSES, 'STATUS')
        ident(self.reason)


@dataclass(frozen=True)
class TransitionAuthorization(Contract):
    HASH = 'authorization_commitment'
    authorization_id: str
    request_commitment: str
    approved_transition: tuple
    authorized_actor: str
    authorization_commitment: str
    schema_version: str = 'agt009-v1'

    def validate(self):
        ident(self.authorized_actor)
        need(type(self.approved_transition) is tuple and self.approved_transition in TRANSITIONS, 'TRANSITION')


@dataclass(frozen=True)
class SupervisionObservation(Contract):
    HASH = 'observation_commitment'
    observation_id: str
    source_component: str
    source_commitment: str
    observed_status: str
    sequence: int
    observation_commitment: str
    schema_version: str = 'agt009-v1'

    def validate(self):
        need(self.source_component == 'AGT008', 'SOURCE')
        need(self.observed_status in ('COORDINATION_RECORDED', 'NOT_QUALIFIED'), 'OBSERVATION')
        integer(self.sequence)


@dataclass(frozen=True)
class SupervisionState(Contract):
    HASH = 'state_commitment'
    active_workflow: WorkflowLifecycle
    agent: AgentLifecycle
    processed_requests: tuple
    confirmed_consumption: int
    uncertain_consumption: int
    reserved_capacity: int
    remaining_budget: int
    history: tuple
    state_commitment: str
    schema_version: str = 'agt009-v1'

    def validate(self):
        for obj, cls in ((self.active_workflow, WorkflowLifecycle), (self.agent, AgentLifecycle)):
            need(type(obj) is cls, 'CONTRACT')
            obj.__post_init__()
        recovery.refs(self.processed_requests, 16)
        need(type(self.history) is tuple and len(self.history) == len(self.processed_requests), 'HISTORY')
        for value in (self.confirmed_consumption, self.uncertain_consumption,
                      self.reserved_capacity, self.remaining_budget):
            integer(value)


@dataclass(frozen=True)
class SupervisionVerdict(Contract):
    HASH = 'verdict_commitment'
    transition_status: str
    reason_code: str
    verification_status: str
    verdict_commitment: str
    production_authorized: bool = False
    knowledge_promotion_authorized: bool = False
    schema_version: str = 'agt009-v1'

    def validate(self):
        need(self.transition_status in ('ALLOW_RECORD', 'REJECT', 'PAUSE_RECOMMENDED',
             'ESCALATE_REQUIRED', 'TERMINATE_RECOMMENDED', 'NOT_QUALIFIED'), 'VERDICT')
        ident(self.reason_code)
        need(self.verification_status == 'NOT_ESTABLISHED', 'TRUST')
        need(self.production_authorized is False and self.knowledge_promotion_authorized is False, 'AUTHORITY')
