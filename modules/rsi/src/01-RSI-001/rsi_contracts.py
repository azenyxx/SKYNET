"""Proposal-only contracts. No authority or execution mechanism."""
from dataclasses import dataclass,fields
import integrated_qualification as q
need,ident,integer,refs,hashcheck=q.need,q.ident,q.integer,q.refs,q.hashcheck
FLAGS=q.FLAGS+('self_modification_authorized',)
DENIED=('SOURCE_REWRITE','MODEL_UPDATE','LEARNING_EXECUTION','KNOWLEDGE_PROMOTION','STRATEGY_ACTIVATION','POLICY_MODIFICATION','PRODUCTION_DEPLOYMENT','SELF_ACCEPTANCE','SELF_AUTHORIZATION','APPROVAL_MODIFICATION','GATE_DISABLE','P1_SUPPRESSION')
TYPES=('ARCHITECTURE_PROPOSAL','ALGORITHM_PROPOSAL','TEST_PROPOSAL')
CLASSES=('INDEPENDENTLY_VERIFIED','STRUCTURALLY_BOUND','HOST_ATTESTED','REPORTED_ONLY','CONTRADICTED','UNAVAILABLE')
FINDINGS=q.FINDINGS+tuple(('L08-%03d'%n,'P1' if n==1 else 'P2','LRN-008','OPEN','OWNER_REPORTED','ORIGINAL_REPORT_REFERENCE','INDEPENDENT_REMEDIATION_EVIDENCE','NOT_QUALIFIED') for n in range(1,4))
BLOCKERS=tuple(x[0] for x in FINDINGS)
LIFECYCLE=('OBSERVED','HYPOTHESIS_REGISTERED','PROPOSAL_SUBMITTED','STRUCTURAL_VALIDATION','EVIDENCE_ASSESSMENT','RISK_ASSESSMENT','POLICY_ASSESSMENT','ADVISORY_VERDICT')
def digest(x): return q.v.m.t.r.s.replay.learning.memory.digest('RSI001',x)
def seal(cls): return 'state_commitment' if cls.__name__=='ImprovementState' else 'commitment'
def make(cls,**kw):
    field=seal(cls); body=tuple((f.name,kw.get(f.name,f.default)) for f in fields(cls) if f.name!=field)
    return cls(**kw,**{field:digest((cls.__name__,body))})
def check(x,c): need(type(x) is c,'TYPE'); x.__post_init__()
def text(x): need(type(x) is str and 1<=len(x.encode('utf8'))<=2048,'TEXT')
class Contract:
    def __post_init__(self):
        need(self.schema_version=='rsi001-v1','VERSION')
        for f in fields(self):
            x=getattr(self,f.name)
            if f.name.endswith('_id'): ident(x)
            if f.name.endswith('_commitment'): hashcheck(x)
        self.validate(); field=seal(type(self))
        need(getattr(self,field)==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=field))),'COMMITMENT')
@dataclass(frozen=True)
class ImprovementObservation(Contract):
    observation_id:str; component_id:str; component_version:str; observation_type:str; evidence_refs:tuple; observed_metrics:tuple; confidence:tuple; provenance_class:str; source_commitment:str; commitment:str; schema_version:str='rsi001-v1'
    def validate(self):
        ident(self.component_version); need(self.observation_type in ('DEFICIENCY','OPTIMIZATION_OPPORTUNITY'),'TYPE'); refs(self.evidence_refs)
        need(type(self.observed_metrics) is tuple and len(self.observed_metrics)<=8,'METRICS')
        for metric in self.observed_metrics:
            need(type(metric) is tuple and len(metric)==3,'METRIC'); ident(metric[0]); integer(metric[1]); ident(metric[2])
        refs(tuple(x[0] for x in self.observed_metrics))
        need(type(self.confidence) is tuple and len(self.confidence)==2,'CONFIDENCE')
        for x in self.confidence: integer(x)
        need(0<=self.confidence[0]<=self.confidence[1]<=10000 and self.confidence[1]>0,'CONFIDENCE')
        need(self.provenance_class in CLASSES and self.provenance_class!='INDEPENDENTLY_VERIFIED','NO_INDEPENDENT_AUTHORITY')
@dataclass(frozen=True)
class ImprovementHypothesis(Contract):
    hypothesis_id:str; observation_id:str; target_component:str; proposed_mechanism:str; expected_benefit:str; measurable_success_criteria:str; falsification_criteria:str; assumptions:tuple; risk_class:str; commitment:str; schema_version:str='rsi001-v1'
    def validate(self):
        ident(self.target_component)
        for x in (self.proposed_mechanism,self.expected_benefit,self.measurable_success_criteria,self.falsification_criteria): text(x)
        refs(self.assumptions); need(self.risk_class in ('LOW','MEDIUM','HIGH'),'RISK')
@dataclass(frozen=True)
class ChangeProposal(Contract):
    proposal_id:str; hypothesis_id:str; change_type:str; target_component:str; target_version:str; affected_interfaces:tuple; proposed_change_summary:str; compatibility_requirements:tuple; prohibited_effects:tuple; required_authorizations:tuple; commitment:str; schema_version:str='rsi001-v1'
    def validate(self):
        ident(self.target_component); ident(self.target_version); ident(self.change_type); text(self.proposed_change_summary)
        refs(self.affected_interfaces); refs(self.compatibility_requirements)
        need(self.prohibited_effects==DENIED and self.required_authorizations==('EXTERNAL_INDEPENDENT_HUMAN_APPROVAL',),'AUTHORITY')
@dataclass(frozen=True)
class ImprovementEvidence(Contract):
    evidence_id:str; source_stage:str; source_artifact:str; evidence_type:str; provenance_class:str; source_commitment:str; verification_status:str; limitations:tuple; commitment:str; schema_version:str='rsi001-v1'
    def validate(self):
        need(self.source_stage in q.STAGES,'STAGE'); ident(self.source_artifact); need(self.evidence_type=='LOCAL_DIAGNOSTIC','EVIDENCE_TYPE')
        need(self.provenance_class in CLASSES and self.provenance_class!='INDEPENDENTLY_VERIFIED','NO_INDEPENDENT_AUTHORITY')
        need(self.verification_status=='NOT_QUALIFIED','VERIFICATION'); refs(self.limitations); need('INDEPENDENT_PROVENANCE_UNAVAILABLE' in self.limitations,'LIMITATION')
@dataclass(frozen=True)
class ImprovementRiskAssessment(Contract):
    proposal_id:str; regression_risks:tuple; security_risks:tuple; capability_boundary_risks:tuple; dependency_risks:tuple; rollback_requirements:tuple; unresolved_blockers:tuple; commitment:str; schema_version:str='rsi001-v1'
    def validate(self):
        for x in (self.regression_risks,self.security_risks,self.capability_boundary_risks,self.dependency_risks,self.rollback_requirements): refs(x)
        need(self.unresolved_blockers==BLOCKERS,'P1_SUPPRESSION')
@dataclass(frozen=True)
class ImprovementPolicy(Contract):
    policy_version:str; permitted_proposal_types:tuple; prohibited_operations:tuple; evidence_requirements:tuple; risk_thresholds:str; resource_limits:int; required_approval_classes:tuple; commitment:str; schema_version:str='rsi001-v1'
    def validate(self):
        ident(self.policy_version); refs(self.permitted_proposal_types); need(set(self.permitted_proposal_types)<=set(TYPES),'PROPOSAL_TYPES')
        need(self.prohibited_operations==DENIED and self.evidence_requirements==('INDEPENDENT_PROVENANCE','ORIGINAL_ARTIFACTS') and self.required_approval_classes==('EXTERNAL_INDEPENDENT_HUMAN_APPROVAL',),'POLICY_RELAXATION')
        need(self.risk_thresholds in ('LOW','MEDIUM'),'RISK_LIMIT'); integer(self.resource_limits); need(1<=self.resource_limits<=64,'BUDGET')
@dataclass(frozen=True)
class ImprovementState(Contract):
    state_version:str; sequence:int; previous_state_commitment:str; registered_proposal_ids:tuple; evaluated_proposal_ids:tuple; rejected_proposal_ids:tuple; cumulative_resource_usage:int; policy_commitment:str; history:tuple; state_commitment:str; schema_version:str='rsi001-v1'
    def validate(self):
        need(self.state_version=='rsi-state-v1','STATE_VERSION'); integer(self.sequence); integer(self.cumulative_resource_usage)
        for x in (self.registered_proposal_ids,self.evaluated_proposal_ids,self.rejected_proposal_ids): refs(x)
        need(self.evaluated_proposal_ids==self.registered_proposal_ids and set(self.rejected_proposal_ids)<=set(self.registered_proposal_ids),'STATE_SETS')
        need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.registered_proposal_ids) and self.cumulative_resource_usage==self.sequence*2,'ACCOUNTING')
        for h in self.history: hashcheck(h)
@dataclass(frozen=True)
class ImprovementVerdict(Contract):
    proposal_id:str; structural_validity:bool; evidence_qualification:str; policy_compliance:bool; risk_classification:str; unresolved_findings:tuple; decision:str; decision_reasons:tuple; authorization_flags:tuple; commitment:str; schema_version:str='rsi001-v1'
    def validate(self):
        need(type(self.structural_validity) is bool and type(self.policy_compliance) is bool,'BOOL')
        need(self.evidence_qualification=='NOT_QUALIFIED','EVIDENCE'); need(self.risk_classification in ('LOW','MEDIUM','HIGH'),'RISK')
        need(self.unresolved_findings==BLOCKERS,'FINDINGS'); refs(self.decision_reasons)
        need(self.decision in ('STRUCTURALLY_VALID','REQUIRES_EVIDENCE','POLICY_BLOCKED','RISK_BLOCKED','INTEGRATION_NOT_QUALIFIED','REJECTED'),'DECISION')
        need(type(self.authorization_flags) is tuple and len(self.authorization_flags)==len(FLAGS),'FLAGS')
        for pair,name in zip(self.authorization_flags,FLAGS): need(type(pair) is tuple and len(pair)==2 and pair[0]==name and pair[1] is False,'AUTHORITY')
