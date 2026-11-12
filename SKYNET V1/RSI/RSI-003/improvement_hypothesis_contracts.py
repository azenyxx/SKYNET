"""Advisory contracts; no execution authority."""
from dataclasses import dataclass,fields
import self_assessment_contracts as s
r=s.r
need,ident,integer,refs,hashcheck=s.need,s.ident,s.integer,s.refs,s.hashcheck
FLAGS=s.FLAGS
BLOCKERS=s.BLOCKERS+('RSI02-001','RSI02-002','RSI02-003')
MECHANISMS=('ALGORITHM_REFINEMENT','RESOURCE_OPTIMIZATION','RELIABILITY_IMPROVEMENT','VALIDATION_STRENGTHENING','INTEGRATION_REPAIR','EVIDENCE_RECOVERY','INTERFACE_REFINEMENT','UNKNOWN')
DECISIONS=('STRUCTURALLY_VALID','REQUIRES_EVIDENCE','BASELINE_REQUIRED','CONTRADICTED','RISK_BLOCKED','POLICY_BLOCKED','INTEGRATION_NOT_QUALIFIED','REJECTED')
def digest(v):return s.digest(('RSI003-v1',v))
def seal(c):return 'state_commitment' if c is ProposalState else 'commitment'
def make(c,**kw):
 k=seal(c);return c(**kw,**{k:digest((c.__name__,tuple((f.name,kw.get(f.name,f.default)) for f in fields(c) if f.name!=k)))})
def check(x,c):need(type(x) is c,'TYPE');x.__post_init__()
def strings(v):refs(v);need(len(v)<=32,'BOUND')
class Contract:
 def __post_init__(self):
  need(self.schema_version=='rsi003-v1','VERSION')
  for f in fields(self):
   v=getattr(self,f.name)
   if f.name.endswith('_id'):ident(v)
   if f.name.endswith('_commitment'):hashcheck(v)
  self.validate();k=seal(type(self));hashcheck(getattr(self,k));need(getattr(self,k)==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=k))),'COMMITMENT')
@dataclass(frozen=True)
class HypothesisCandidate(Contract):
 hypothesis_id:str;source_bottleneck_id:str;target_component:str;proposed_mechanism:str;expected_effect:str;assumptions:tuple;evidence_refs:tuple;source_commitment:str;commitment:str;schema_version:str='rsi003-v1'
 def validate(self):
  ident(self.target_component);need(self.proposed_mechanism in MECHANISMS,'MECHANISM');need(self.expected_effect=='TEST_LOCAL_DEFICIENCY_REDUCTION','EFFECT');strings(self.assumptions);strings(self.evidence_refs)
@dataclass(frozen=True)
class HypothesisEvidence(Contract):
 evidence_id:str;hypothesis_id:str;source_stage:str;evidence_type:str;provenance_class:str;verification_status:str;supports_or_contradicts:str;source_commitment:str;limitations:tuple;commitment:str;schema_version:str='rsi003-v1'
 def validate(self):
  need(self.source_stage=='RSI-002' and self.evidence_type=='LOCAL_DIAGNOSTIC','SOURCE');s.provenance(self.provenance_class);need(self.verification_status=='NOT_INDEPENDENTLY_QUALIFIED','VERIFICATION');need(self.supports_or_contradicts in ('UNVERIFIED_SUPPORT','CONTRADICTS','UNAVAILABLE'),'RELATION');strings(self.limitations);need('INDEPENDENT_PROVENANCE_UNAVAILABLE' in self.limitations,'LIMITATION')
@dataclass(frozen=True)
class ImprovementPrediction(Contract):
 hypothesis_id:str;target_metric:str;baseline_reference:str;predicted_direction:str;predicted_magnitude:tuple;measurement_requirements:tuple;uncertainty_class:str;falsification_conditions:tuple;commitment:str;schema_version:str='rsi003-v1'
 def validate(self):
  ident(self.target_metric);need(type(self.baseline_reference) is str,'BASELINE')
  if self.baseline_reference:ident(self.baseline_reference)
  need(self.predicted_direction in ('HIGHER','LOWER'),'DIRECTION');need(self.predicted_magnitude==() and type(self.predicted_magnitude) is tuple,'NO_QUANTIFIED_GAIN')
  need(self.measurement_requirements==('PINNED_BASELINE','MATCHED_UNITS_POPULATION','OFFLINE_CONTROLLED_TEST'),'MEASUREMENTS');need(self.uncertainty_class=='NOT_MEASURED','UNCERTAINTY');need(self.falsification_conditions==('NO_IMPROVEMENT_AGAINST_BASELINE','REGRESSION_ON_RETAINED_CAPABILITIES'),'FALSIFICATION')
@dataclass(frozen=True)
class ImprovementProposal(Contract):
 proposal_id:str;hypothesis_id:str;target_component:str;target_version:str;change_type:str;change_summary:str;affected_interfaces:tuple;required_evidence:tuple;required_authorizations:tuple;commitment:str;schema_version:str='rsi003-v1'
 def validate(self):
  ident(self.target_component);ident(self.target_version);need(self.change_type in MECHANISMS,'MECHANISM');need(self.change_summary=='ADVISORY_TEST_PROPOSAL_ONLY','SUMMARY');strings(self.affected_interfaces);need(self.required_evidence==('BASELINE','INDEPENDENT_VERIFICATION','REGRESSION_TESTS'),'EVIDENCE');need(self.required_authorizations==('EXTERNAL_INDEPENDENT_HUMAN_APPROVAL',),'AUTHORITY')
@dataclass(frozen=True)
class ProposalDependency(Contract):
 proposal_id:str;prerequisite_proposals:tuple;affected_components:tuple;inherited_findings:tuple;compatibility_requirements:tuple;unresolved_dependencies:tuple;commitment:str;schema_version:str='rsi003-v1'
 def validate(self):
  for v in (self.prerequisite_proposals,self.affected_components,self.compatibility_requirements,self.unresolved_dependencies):strings(v)
  need(self.proposal_id not in self.prerequisite_proposals,'CYCLE');need(self.inherited_findings==BLOCKERS,'FINDINGS')
@dataclass(frozen=True)
class ProposalRiskAssessment(Contract):
 proposal_id:str;regression_risks:tuple;security_risks:tuple;authorization_risks:tuple;integration_risks:tuple;evidence_gaps:tuple;rollback_requirements:tuple;commitment:str;schema_version:str='rsi003-v1'
 def validate(self):
  for f in ('regression_risks','security_risks','authorization_risks','integration_risks','evidence_gaps','rollback_requirements'):strings(getattr(self,f))
@dataclass(frozen=True)
class ProposalState(Contract):
 state_version:str;sequence:int;previous_state_commitment:str;registered_hypotheses:tuple;registered_proposals:tuple;rejected_proposals:tuple;cumulative_resource_usage:int;budget:int;history:tuple;state_commitment:str;schema_version:str='rsi003-v1'
 def validate(self):
  need(self.state_version=='state-v1','STATE');integer(self.sequence);integer(self.cumulative_resource_usage);integer(self.budget);need(1<=self.budget<=64 and self.cumulative_resource_usage<=self.budget,'BUDGET')
  for v in (self.registered_hypotheses,self.registered_proposals,self.rejected_proposals):strings(v)
  need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.registered_hypotheses)==len(self.registered_proposals),'STATE');need(self.cumulative_resource_usage==self.sequence*2,'ACCOUNTING');need(set(self.rejected_proposals)<=set(self.registered_proposals),'STATE')
  for h in self.history:hashcheck(h)
@dataclass(frozen=True)
class ProposalVerdict(Contract):
 proposal_id:str;structural_validity:bool;hypothesis_qualification:str;evidence_qualification:str;prediction_qualification:str;risk_classification:str;unresolved_findings:tuple;decision:str;decision_reasons:tuple;authorization_flags:tuple;commitment:str;schema_version:str='rsi003-v1'
 def validate(self):
  need(self.structural_validity is True,'STRUCTURE');need(self.hypothesis_qualification in ('PLAUSIBLE_UNVERIFIED','CONTRADICTED','UNSUPPORTED'),'HYPOTHESIS');need(self.evidence_qualification=='NOT_INDEPENDENTLY_QUALIFIED','EVIDENCE');need(self.prediction_qualification in ('BASELINE_REQUIRED','UNVERIFIED_BASELINE'),'PREDICTION');need(self.risk_classification in ('NOT_QUALIFIED','BLOCKED'),'RISK');need(self.unresolved_findings==BLOCKERS,'FINDINGS');need(self.decision in DECISIONS,'DECISION');strings(self.decision_reasons)
  need(type(self.authorization_flags) is tuple and len(self.authorization_flags)==7,'FLAGS')
  for p,n in zip(self.authorization_flags,FLAGS):need(type(p) is tuple and len(p)==2 and p[0]==n and p[1] is False,'AUTHORITY')
