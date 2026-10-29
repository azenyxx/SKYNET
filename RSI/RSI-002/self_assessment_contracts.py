"""Immutable diagnostic contracts; hashes do not establish authority."""
from dataclasses import dataclass, fields
import rsi_contracts as r
need,ident,integer,refs,hashcheck=r.need,r.ident,r.integer,r.refs,r.hashcheck
TYPES=('PERFORMANCE','RELIABILITY','CORRECTNESS','RESOURCE_EFFICIENCY','INTEGRATION','EVIDENCE_QUALITY','SECURITY_BOUNDARY','LEARNING_QUALITY','UNKNOWN')
BLOCKERS=r.BLOCKERS+('RSI01-001','RSI01-002','RSI01-003')
FLAGS=r.FLAGS
CLASSES=r.CLASSES

def digest(v): return r.digest(('RSI002-v1',v))
def seal(c): return 'snapshot_commitment' if c is ComponentSnapshot else 'state_commitment' if c is AssessmentState else 'commitment'
def make(c,**kw):
    key=seal(c); body=tuple((f.name,kw.get(f.name,f.default)) for f in fields(c) if f.name!=key)
    return c(**kw,**{key:digest((c.__name__,body))})
def check(x,c): need(type(x) is c,'TYPE'); x.__post_init__()
def strings(x): refs(x); need(len(x)<=32,'BOUND')
def provenance(x): need(type(x) is str and x in CLASSES and x!='INDEPENDENTLY_VERIFIED','NO_INDEPENDENT_AUTHORITY')
class Contract:
    def __post_init__(self):
        need(self.schema_version=='rsi002-v1','VERSION')
        for f in fields(self):
            v=getattr(self,f.name)
            if f.name.endswith('_id'): ident(v)
            if f.name.endswith('_commitment'): hashcheck(v)
        self.validate(); key=seal(type(self)); hashcheck(getattr(self,key))
        need(getattr(self,key)==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=key))),'COMMITMENT')
@dataclass(frozen=True)
class ComponentSnapshot(Contract):
    component_id:str; component_version:str; capability_ids:tuple; interface_commitments:tuple; known_findings:tuple; evidence_refs:tuple; snapshot_commitment:str; schema_version:str='rsi002-v1'
    def validate(self):
        ident(self.component_version)
        for v in (self.capability_ids,self.interface_commitments,self.evidence_refs): strings(v)
        for v in self.interface_commitments: hashcheck(v)
        need(self.known_findings==BLOCKERS,'FINDINGS')
@dataclass(frozen=True)
class AssessmentMetric(Contract):
    metric_id:str; component_id:str; metric_name:str; value:int; unit:str; measurement_context:str; measurement_source:str; provenance_class:str; qualification_status:str; commitment:str; schema_version:str='rsi002-v1'
    def validate(self):
        for v in (self.metric_name,self.unit,self.measurement_context,self.measurement_source): ident(v)
        integer(self.value); need(self.value<=1000000,'VALUE'); provenance(self.provenance_class)
        need(self.qualification_status in ('DIAGNOSTIC','REPORTED','UNAVAILABLE'),'QUALIFICATION')
@dataclass(frozen=True)
class BottleneckObservation(Contract):
    bottleneck_id:str; component_id:str; bottleneck_type:str; affected_capabilities:tuple; supporting_evidence:tuple; observed_impact:str; confidence_class:str; source_commitment:str; commitment:str; schema_version:str='rsi002-v1'
    def validate(self):
        need(self.bottleneck_type in TYPES,'CATEGORY'); strings(self.affected_capabilities); strings(self.supporting_evidence)
        need(self.observed_impact in ('UNKNOWN','LOCAL_DIAGNOSTIC'),'IMPACT'); need(self.confidence_class in ('SUSPECTED','CONTRADICTED','UNSUPPORTED'),'CONFIDENCE')
@dataclass(frozen=True)
class BottleneckEvidence(Contract):
    evidence_id:str; observation_id:str; source_stage:str; evidence_type:str; provenance_class:str; verification_status:str; source_commitment:str; limitations:tuple; commitment:str; schema_version:str='rsi002-v1'
    def validate(self):
        need(self.source_stage=='RSI-001','STAGE'); need(self.evidence_type=='LOCAL_DIAGNOSTIC','TYPE'); provenance(self.provenance_class)
        need(self.verification_status=='NOT_INDEPENDENTLY_QUALIFIED','VERIFICATION'); strings(self.limitations)
        need('INDEPENDENT_PROVENANCE_UNAVAILABLE' in self.limitations,'LIMITATIONS')
@dataclass(frozen=True)
class DependencyImpact(Contract):
    bottleneck_id:str; upstream_dependencies:tuple; downstream_dependencies:tuple; affected_interfaces:tuple; possible_failure_modes:tuple; impact_class:str; qualification_gaps:tuple; commitment:str; schema_version:str='rsi002-v1'
    def validate(self):
        for v in (self.upstream_dependencies,self.downstream_dependencies,self.affected_interfaces,self.possible_failure_modes,self.qualification_gaps): strings(v)
        need(self.impact_class=='DECLARED_NOT_VERIFIED','IMPACT')
        need(not set(self.upstream_dependencies)&set(self.downstream_dependencies),'DEPENDENCY_CYCLE')
@dataclass(frozen=True)
class AssessmentPolicy(Contract):
    policy_version:str; permitted_assessment_types:tuple; evidence_requirements:tuple; classification_rules:str; resource_limits:int; prohibited_operations:tuple; inherited_blockers:tuple; commitment:str; schema_version:str='rsi002-v1'
    def validate(self):
        ident(self.policy_version); strings(self.permitted_assessment_types); need(set(self.permitted_assessment_types)<=set(TYPES),'CATEGORY')
        need(self.evidence_requirements==('ORIGINAL_RSI001','NO_INDEPENDENT_CLAIM') and self.classification_rules=='ordinal-v1','POLICY')
        integer(self.resource_limits); need(1<=self.resource_limits<=64,'BUDGET')
        need(self.prohibited_operations==r.DENIED and self.inherited_blockers==BLOCKERS,'AUTHORITY')
@dataclass(frozen=True)
class AssessmentState(Contract):
    state_version:str; sequence:int; previous_state_commitment:str; assessed_components:tuple; registered_bottlenecks:tuple; cumulative_resource_usage:int; policy_commitment:str; history:tuple; state_commitment:str; schema_version:str='rsi002-v1'
    def validate(self):
        need(self.state_version=='state-v1','STATE'); integer(self.sequence); integer(self.cumulative_resource_usage)
        strings(self.assessed_components); strings(self.registered_bottlenecks)
        need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.assessed_components)==len(self.registered_bottlenecks),'STATE')
        need(self.cumulative_resource_usage>=self.sequence,'ACCOUNTING')
        for h in self.history: hashcheck(h)
@dataclass(frozen=True)
class AssessmentVerdict(Contract):
    component_id:str; identified_bottlenecks:tuple; evidence_qualification:str; dependency_assessment:str; priority_order:tuple; unresolved_findings:tuple; assessment_status:str; decision_reasons:tuple; authorization_flags:tuple; commitment:str; schema_version:str='rsi002-v1'
    def validate(self):
        strings(self.identified_bottlenecks); strings(self.priority_order); strings(self.decision_reasons)
        need(self.identified_bottlenecks==self.priority_order and self.unresolved_findings==BLOCKERS,'FINDINGS')
        need(self.evidence_qualification=='NOT_INDEPENDENTLY_QUALIFIED' and self.dependency_assessment=='DECLARED_NOT_VERIFIED','QUALIFICATION')
        need(self.assessment_status in ('SUSPECTED','CONTRADICTED','UNSUPPORTED'),'STATUS')
        need(type(self.authorization_flags) is tuple and len(self.authorization_flags)==7,'FLAGS')
        for p,n in zip(self.authorization_flags,FLAGS): need(type(p) is tuple and len(p)==2 and p[0]==n and p[1] is False,'AUTHORITY')
