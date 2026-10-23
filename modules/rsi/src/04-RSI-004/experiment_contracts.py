"""Bounded diagnostic experiment contracts, not an executable-code sandbox."""
from dataclasses import dataclass,fields
import improvement_hypothesis_contracts as p
need,ident,integer,refs,hashcheck=p.need,p.ident,p.integer,p.refs,p.hashcheck
FLAGS=p.FLAGS
BLOCKERS=p.BLOCKERS+('RSI03-001','RSI03-002','RSI03-003')
TYPES=('METRIC_COMPARISON','REGRESSION_CHECK','RELIABILITY_COMPARISON','RESOURCE_COMPARISON','INTERFACE_COMPATIBILITY_CHECK','EVIDENCE_QUALIFICATION')
OUTCOMES=('IMPROVEMENT_OBSERVED','REGRESSION_OBSERVED','NO_MEASURABLE_CHANGE','INCONCLUSIVE','NOT_COMPARABLE','EVIDENCE_REQUIRED','POLICY_BLOCKED')
DENIED=p.r.DENIED+('SHELL','NETWORK','PROCESS_SPAWN','DYNAMIC_IMPORT','CANDIDATE_EXECUTION')
def digest(v):return p.digest(('RSI004-v1',v))
def seal(c):return 'state_commitment' if c is ExperimentState else 'comparison_commitment' if c is ExperimentComparison else 'commitment'
def make(c,**kw):
 k=seal(c);return c(**kw,**{k:digest((c.__name__,tuple((f.name,kw.get(f.name,f.default)) for f in fields(c) if f.name!=k)))})
def check(x,c):need(type(x) is c,'TYPE');x.__post_init__()
def strings(x):refs(x);need(len(x)<=40,'BOUND')
def number(x):need(type(x) is int and abs(x)<=2000000,'INTEGER_PRECISION_BOUND')
class Contract:
 def __post_init__(self):
  need(self.schema_version=='rsi004-v1','VERSION')
  for f in fields(self):
   v=getattr(self,f.name)
   if f.name.endswith('_id'):ident(v)
   if f.name.endswith('_commitment'):hashcheck(v)
  self.validate();k=seal(type(self));hashcheck(getattr(self,k));need(getattr(self,k)==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=k))),'COMMITMENT')
@dataclass(frozen=True)
class ExperimentSpecification(Contract):
 experiment_id:str;proposal_id:str;hypothesis_id:str;target_component:str;target_version:str;candidate_version:str;experiment_type:str;baseline_ref:str;candidate_ref:str;target_metrics:tuple;success_criteria:str;falsification_criteria:str;resource_limits:int;source_commitment:str;commitment:str;schema_version:str='rsi004-v1'
 def validate(self):
  for x in (self.target_component,self.target_version,self.candidate_version):ident(x)
  need(self.experiment_type in TYPES,'TYPE');hashcheck(self.baseline_ref);hashcheck(self.candidate_ref);need(self.baseline_ref!=self.candidate_ref,'SUBJECT_IDENTITY')
  need(type(self.target_metrics) is tuple and 1<=len(self.target_metrics)<=8,'METRICS')
  for row in self.target_metrics:
   need(type(row) is tuple and len(row)==4,'METRIC_SCHEMA');ident(row[0]);ident(row[1]);need(row[2] in ('HIGHER','LOWER'),'DIRECTION');ident(row[3])
  strings(tuple(x[0] for x in self.target_metrics));need(self.success_criteria=='IMPROVEMENT_WITHOUT_REGRESSION' and self.falsification_criteria=='ANY_REGRESSION_OR_NO_IMPROVEMENT','CRITERIA');integer(self.resource_limits);need(1<=self.resource_limits<=64,'BUDGET')
@dataclass(frozen=True)
class ExperimentEnvironment(Contract):
 environment_id:str;environment_version:str;runtime_fingerprint:str;dependency_commitments:tuple;configuration_commitment:str;isolation_class:str;permitted_operations:tuple;prohibited_operations:tuple;commitment:str;schema_version:str='rsi004-v1'
 def validate(self):
  ident(self.environment_version);hashcheck(self.runtime_fingerprint);strings(self.dependency_commitments)
  for x in self.dependency_commitments:hashcheck(x)
  need(self.isolation_class=='PURE_DATA_INTERFACE_NO_OS_ISOLATION' and self.permitted_operations==('COMPARE_SUPPLIED_OBSERVATIONS',) and self.prohibited_operations==DENIED,'ISOLATION_POLICY')
@dataclass(frozen=True)
class ExperimentMeasurement(Contract):
 measurement_id:str;experiment_id:str;subject_type:str;subject_commitment:str;component_id:str;component_version:str;metric_id:str;metric_value:int;metric_unit:str;measurement_context:str;provenance_class:str;verification_status:str;source_commitment:str;commitment:str;schema_version:str='rsi004-v1'
 def validate(self):
  need(self.subject_type in ('BASELINE','CANDIDATE'),'SUBJECT');ident(self.component_version);ident(self.metric_unit);ident(self.measurement_context);number(self.metric_value);need(abs(self.metric_value)<=1000000,'VALUE');p.s.provenance(self.provenance_class);need(self.verification_status in ('DIAGNOSTIC','REPORTED','UNAVAILABLE'),'VERIFICATION')
@dataclass(frozen=True)
class ExperimentComparison(Contract):
 experiment_id:str;baseline_measurement_id:str;candidate_measurement_id:str;metric_id:str;metric_direction:str;baseline_value:int;candidate_value:int;observed_delta:int;comparability_status:str;comparison_commitment:str;schema_version:str='rsi004-v1'
 def validate(self):
  need(self.metric_direction in ('HIGHER','LOWER'),'DIRECTION')
  for x in (self.baseline_value,self.candidate_value,self.observed_delta):number(x)
  need(self.observed_delta==self.candidate_value-self.baseline_value,'DELTA');need(self.comparability_status=='COMPARABLE_DIAGNOSTIC','COMPARABILITY')
@dataclass(frozen=True)
class ExperimentRiskAssessment(Contract):
 experiment_id:str;resource_risks:tuple;regression_risks:tuple;security_risks:tuple;provenance_gaps:tuple;isolation_limitations:tuple;unresolved_blockers:tuple;commitment:str;schema_version:str='rsi004-v1'
 def validate(self):
  for x in (self.resource_risks,self.regression_risks,self.security_risks,self.provenance_gaps,self.isolation_limitations):strings(x)
  need(self.unresolved_blockers==BLOCKERS,'FINDINGS')
@dataclass(frozen=True)
class ExperimentPolicy(Contract):
 policy_version:str;permitted_experiment_types:tuple;permitted_measurement_types:tuple;evidence_requirements:tuple;comparison_rules:str;resource_limits:int;prohibited_operations:tuple;required_authorizations:tuple;commitment:str;schema_version:str='rsi004-v1'
 def validate(self):
  ident(self.policy_version);strings(self.permitted_experiment_types);need(set(self.permitted_experiment_types)<=set(TYPES),'TYPE');need(self.permitted_measurement_types==('DIAGNOSTIC','REPORTED','UNAVAILABLE') and self.evidence_requirements==('ORIGINAL_PROPOSAL_REPLAY','NO_AUTHENTICITY_INFERENCE') and self.comparison_rules=='integer-exact-v1','POLICY');integer(self.resource_limits);need(1<=self.resource_limits<=64,'BUDGET');need(self.prohibited_operations==DENIED and self.required_authorizations==('NO_ADOPTION_AUTHORITY',),'AUTHORITY')
@dataclass(frozen=True)
class ExperimentState(Contract):
 state_version:str;sequence:int;previous_state_commitment:str;registered_experiments:tuple;evaluated_experiments:tuple;rejected_experiments:tuple;cumulative_resource_usage:int;policy_commitment:str;history:tuple;state_commitment:str;schema_version:str='rsi004-v1'
 def validate(self):
  need(self.state_version=='state-v1','STATE');integer(self.sequence);integer(self.cumulative_resource_usage)
  for x in (self.registered_experiments,self.evaluated_experiments,self.rejected_experiments):strings(x)
  need(self.registered_experiments==self.evaluated_experiments and set(self.rejected_experiments)<=set(self.registered_experiments),'STATE');need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.registered_experiments) and self.cumulative_resource_usage>=self.sequence,'ACCOUNTING')
  for x in self.history:hashcheck(x)
@dataclass(frozen=True)
class ExperimentVerdict(Contract):
 experiment_id:str;structural_validity:bool;evidence_qualification:str;environment_qualification:str;comparison_status:str;regression_status:str;observed_outcome:str;unresolved_findings:tuple;decision:str;decision_reasons:tuple;authorization_flags:tuple;commitment:str;schema_version:str='rsi004-v1'
 def validate(self):
  need(self.structural_validity is True,'STRUCTURE');need(self.evidence_qualification=='NOT_INDEPENDENTLY_QUALIFIED' and self.environment_qualification=='INTERFACE_ONLY','QUALIFICATION');need(self.comparison_status in ('COMPLETE','INCOMPLETE','NOT_COMPARABLE'),'STATUS');need(self.regression_status in ('OBSERVED','NOT_OBSERVED','NOT_QUALIFIED'),'REGRESSION');need(self.observed_outcome in OUTCOMES and self.decision=='ADVISORY_NOT_AUTHORIZED','DECISION');need(self.unresolved_findings==BLOCKERS,'FINDINGS');strings(self.decision_reasons)
  need(type(self.authorization_flags) is tuple and len(self.authorization_flags)==7,'FLAGS')
  for pair,name in zip(self.authorization_flags,FLAGS):need(type(pair) is tuple and len(pair)==2 and pair[0]==name and pair[1] is False,'AUTHORITY')
