"""Frozen diagnostic gate contracts; commitments are not authenticity."""
from dataclasses import dataclass,fields
import experiment_contracts as e
need,ident,integer,refs,hashcheck=e.need,e.ident,e.integer,e.refs,e.hashcheck
FLAGS=e.FLAGS
BLOCKERS=e.BLOCKERS+('RSI04-001','RSI04-002','RSI04-003')
GATES=('METRIC_REGRESSION','PERFORMANCE_ACCEPTANCE','RELIABILITY','CORRECTNESS','INTERFACE_COMPATIBILITY','EVIDENCE_QUALITY','SAFETY_BOUNDARY','INHERITED_BLOCKERS')
OUTCOMES=('PASS','FAIL','INCONCLUSIVE','NOT_QUALIFIED','POLICY_BLOCKED')
DECISIONS=('LOCAL_GATES_PASSED','REGRESSION_DETECTED','EVIDENCE_REQUIRED','NOT_COMPARABLE','INTEGRATION_NOT_QUALIFIED','POLICY_BLOCKED','REJECTED')
def digest(x):return e.digest(('RSI005-v1',x))
def seal(c):return 'state_commitment' if c is EvaluationState else 'gate_commitment' if c is RegressionGate else 'commitment'
def make(c,**kw):
 k=seal(c);return c(**kw,**{k:digest((c.__name__,tuple((f.name,kw.get(f.name,f.default)) for f in fields(c) if f.name!=k)))})
def check(x,c):need(type(x) is c,'TYPE');x.__post_init__()
def strings(x):refs(x);need(len(x)<=40,'BOUND')
class Contract:
 def __post_init__(self):
  need(self.schema_version=='rsi005-v1','VERSION')
  for f in fields(self):
   x=getattr(self,f.name)
   if f.name.endswith('_id'):ident(x)
   if f.name.endswith('_commitment'):hashcheck(x)
  self.validate();k=seal(type(self));hashcheck(getattr(self,k));need(getattr(self,k)==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=k))),'COMMITMENT')
@dataclass(frozen=True)
class EvaluationSpecification(Contract):
 evaluation_id:str;proposal_id:str;experiment_id:str;baseline_commitment:str;candidate_commitment:str;required_metric_ids:tuple;required_gate_ids:tuple;evaluation_policy_version:str;source_commitment:str;commitment:str;schema_version:str='rsi005-v1'
 def validate(self):
  strings(self.required_metric_ids);strings(self.required_gate_ids);need(1<=len(self.required_metric_ids)<=8 and 1<=len(self.required_gate_ids)<=8,'BOUND');ident(self.evaluation_policy_version);need(self.baseline_commitment!=self.candidate_commitment,'IDENTITY')
@dataclass(frozen=True)
class EvaluationMetric(Contract):
 metric_id:str;baseline_measurement_ref:str;candidate_measurement_ref:str;unit:str;optimization_direction:str;baseline_value:int;candidate_value:int;comparison_context:str;provenance_class:str;verification_status:str;commitment:str;schema_version:str='rsi005-v1'
 def validate(self):
  for x in (self.baseline_measurement_ref,self.candidate_measurement_ref,self.unit,self.comparison_context):ident(x)
  e.number(self.baseline_value);e.number(self.candidate_value);need(self.optimization_direction in ('HIGHER','LOWER'),'DIRECTION');e.p.s.provenance(self.provenance_class);need(self.verification_status=='SUPPLIED_DIAGNOSTIC','VERIFICATION')
@dataclass(frozen=True)
class RegressionThreshold(Contract):
 metric_id:str;threshold_type:str;maximum_allowed_regression:int;minimum_required_improvement:int;threshold_unit:str;threshold_source:str;qualification_status:str;commitment:str;schema_version:str='rsi005-v1'
 def validate(self):
  need(self.threshold_type=='ABSOLUTE_INTEGER','TYPE');integer(self.maximum_allowed_regression);integer(self.minimum_required_improvement);need(max(self.maximum_allowed_regression,self.minimum_required_improvement)<=1000000,'BOUND');ident(self.threshold_unit);ident(self.threshold_source);need(self.qualification_status=='HOST_POLICY_DIAGNOSTIC','QUALIFICATION')
@dataclass(frozen=True)
class RegressionGate(Contract):
 gate_id:str;gate_type:str;required_metrics:tuple;threshold_refs:tuple;evidence_requirements:tuple;failure_conditions:tuple;inherited_blockers:tuple;gate_commitment:str;schema_version:str='rsi005-v1'
 def validate(self):
  need(self.gate_type in GATES,'TYPE');strings(self.required_metrics);strings(self.threshold_refs)
  for x in self.threshold_refs:hashcheck(x)
  need(self.evidence_requirements==('COMPLETE_SOURCE_REPLAY',) and self.failure_conditions==('ANY_REQUIRED_FAILURE',) and self.inherited_blockers==BLOCKERS,'POLICY')
@dataclass(frozen=True)
class ComparativeEvidence(Contract):
 evidence_id:str;evaluation_id:str;source_stage:str;source_artifact:str;evidence_type:str;provenance_class:str;verification_status:str;source_commitment:str;limitations:tuple;commitment:str;schema_version:str='rsi005-v1'
 def validate(self):
  need(self.source_stage=='RSI-004' and self.evidence_type=='SUPPLIED_OBSERVATIONS','SOURCE');ident(self.source_artifact);e.p.s.provenance(self.provenance_class);need(self.verification_status=='NOT_INDEPENDENTLY_QUALIFIED','VERIFICATION');strings(self.limitations);need('INDEPENDENT_PROVENANCE_UNAVAILABLE' in self.limitations,'LIMITATION')
@dataclass(frozen=True)
class EvaluationPolicy(Contract):
 policy_version:str;permitted_evaluation_types:tuple;mandatory_gates:tuple;evidence_requirements:tuple;regression_rules:str;resource_limits:int;prohibited_operations:tuple;required_authorizations:tuple;commitment:str;schema_version:str='rsi005-v1'
 def validate(self):
  ident(self.policy_version);need(self.permitted_evaluation_types==('DIAGNOSTIC_COMPARISON',) and self.mandatory_gates==GATES,'GATES');need(self.evidence_requirements==('SOURCE_REPLAY','NO_PROVENANCE_UPGRADE') and self.regression_rules=='EXACT_CONSERVATIVE_V1','RULES');integer(self.resource_limits);need(1<=self.resource_limits<=64,'BUDGET');need(self.prohibited_operations==e.DENIED and self.required_authorizations==('NO_ADOPTION_AUTHORITY',),'AUTHORITY')
@dataclass(frozen=True)
class EvaluationState(Contract):
 state_version:str;sequence:int;previous_state_commitment:str;evaluated_proposals:tuple;rejected_evaluations:tuple;cumulative_resource_usage:int;policy_commitment:str;evaluation_ids:tuple;history:tuple;state_commitment:str;schema_version:str='rsi005-v1'
 def validate(self):
  need(self.state_version=='state-v1','STATE');integer(self.sequence);integer(self.cumulative_resource_usage)
  for x in (self.evaluated_proposals,self.rejected_evaluations,self.evaluation_ids):strings(x)
  need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.evaluated_proposals)==len(self.evaluation_ids),'STATE');need(set(self.rejected_evaluations)<=set(self.evaluation_ids) and self.cumulative_resource_usage>=self.sequence,'ACCOUNTING')
  for x in self.history:hashcheck(x)
@dataclass(frozen=True)
class EvaluationVerdict(Contract):
 evaluation_id:str;proposal_id:str;metric_results:tuple;gate_results:tuple;regression_status:str;evidence_qualification:str;compatibility_status:str;safety_status:str;unresolved_findings:tuple;decision:str;decision_reasons:tuple;authorization_flags:tuple;commitment:str;schema_version:str='rsi005-v1'
 def validate(self):
  need(type(self.metric_results) is tuple and len(self.metric_results)<=8,'METRICS')
  for row in self.metric_results:need(type(row) is tuple and len(row)==4,'METRIC');ident(row[0]);e.number(row[1]);need(row[2] in OUTCOMES and row[3] in OUTCOMES,'RESULT')
  strings(tuple(x[0] for x in self.metric_results));need(type(self.gate_results) is tuple and len(self.gate_results)==8,'GATES')
  for row in self.gate_results:need(type(row) is tuple and len(row)==2 and row[0] in GATES and row[1] in OUTCOMES,'GATE')
  need(tuple(x[0] for x in self.gate_results)==tuple(sorted(GATES)),'GATE_ORDER');need(self.regression_status in ('OBSERVED','NOT_OBSERVED','NOT_QUALIFIED'),'REGRESSION');need(self.evidence_qualification=='NOT_INDEPENDENTLY_QUALIFIED' and self.compatibility_status=='NOT_QUALIFIED' and self.safety_status=='NOT_QUALIFIED','QUALIFICATION');need(self.unresolved_findings==BLOCKERS and self.decision in DECISIONS,'DECISION');strings(self.decision_reasons)
  need(type(self.authorization_flags) is tuple and len(self.authorization_flags)==7,'FLAGS')
  for pair,name in zip(self.authorization_flags,FLAGS):need(type(pair) is tuple and len(pair)==2 and pair[0]==name and pair[1] is False,'AUTHORITY')
