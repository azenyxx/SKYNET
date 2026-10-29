"""Descriptive governance records; never an authorization issuer."""
from dataclasses import dataclass,fields
import comparative_evaluation_contracts as q
need,ident,integer,refs,hashcheck=q.need,q.ident,q.integer,q.refs,q.hashcheck
FLAGS=q.FLAGS
BLOCKERS=q.BLOCKERS+('RSI05-001','RSI05-002','RSI05-003')
CRITERIA=('EVIDENCE_QUALITY','EXPECTED_IMPACT','REGRESSION_RISK','DEPENDENCY_READINESS','RESOURCE_COST','SAFETY_READINESS','IMPLEMENTATION_COMPLEXITY')
DECISIONS=('ADVISORY_SELECTED','REQUIRES_EVIDENCE','REQUIRES_HUMAN_REVIEW','GATE_BLOCKED','RISK_BLOCKED','POLICY_BLOCKED','INTEGRATION_NOT_QUALIFIED','NO_ELIGIBLE_CANDIDATE','REJECTED')
def digest(x):return q.digest(('RSI006-v1',x))
def seal(c):return 'state_commitment' if c is GovernanceState else 'ranking_commitment' if c is CandidateRanking else 'commitment'
def make(c,**kw):
 k=seal(c);return c(**kw,**{k:digest((c.__name__,tuple((f.name,kw.get(f.name,f.default)) for f in fields(c) if f.name!=k)))})
def check(x,c):need(type(x) is c,'TYPE');x.__post_init__()
def strings(x):refs(x);need(len(x)<=48,'BOUND')
class Contract:
 def __post_init__(self):
  need(self.schema_version=='rsi006-v1','VERSION')
  for f in fields(self):
   x=getattr(self,f.name)
   if f.name.endswith('_id'):ident(x)
   if f.name.endswith('_commitment'):hashcheck(x)
  self.validate();k=seal(type(self));hashcheck(getattr(self,k));need(getattr(self,k)==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=k))),'COMMITMENT')
@dataclass(frozen=True)
class SelectionCandidate(Contract):
 candidate_id:str;proposal_id:str;proposal_commitment:str;evaluation_id:str;evaluation_commitment:str;target_component:str;target_version:str;evidence_refs:tuple;inherited_findings:tuple;commitment:str;schema_version:str='rsi006-v1'
 def validate(self):
  ident(self.target_component);ident(self.target_version);strings(self.evidence_refs);need(self.inherited_findings==BLOCKERS,'FINDINGS')
@dataclass(frozen=True)
class EligibilityAssessment(Contract):
 candidate_id:str;structural_status:str;evidence_status:str;mandatory_gate_status:str;regression_status:str;policy_status:str;unresolved_blockers:tuple;eligibility_decision:str;decision_reasons:tuple;commitment:str;schema_version:str='rsi006-v1'
 def validate(self):
  need(self.structural_status=='VALID' and self.evidence_status=='NOT_INDEPENDENTLY_QUALIFIED','QUALIFICATION');need(self.mandatory_gate_status in ('FAIL','NOT_QUALIFIED'),'GATES');need(self.regression_status in ('OBSERVED','NOT_OBSERVED','NOT_QUALIFIED'),'REGRESSION');need(self.policy_status in ('BLOCKED','ADVISORY_ONLY'),'POLICY');need(self.unresolved_blockers==BLOCKERS and self.eligibility_decision in ('GATE_BLOCKED','RISK_BLOCKED','POLICY_BLOCKED','REQUIRES_EVIDENCE','INTEGRATION_NOT_QUALIFIED','REJECTED'),'ELIGIBILITY');strings(self.decision_reasons)
@dataclass(frozen=True)
class SelectionCriterion(Contract):
 criterion_id:str;criterion_type:str;comparison_direction:str;evidence_requirements:tuple;qualification_status:str;policy_source:str;commitment:str;schema_version:str='rsi006-v1'
 def validate(self):
  need(self.criterion_type in CRITERIA and self.comparison_direction=='CONSERVATIVE_ORDINAL','CRITERION');need(self.evidence_requirements==('ORIGINAL_GATE_REPLAY',) and self.qualification_status=='DIAGNOSTIC_ONLY','EVIDENCE');ident(self.policy_source)
@dataclass(frozen=True)
class CandidateRanking(Contract):
 candidate_id:str;eligibility_class:str;criterion_results:tuple;priority_class:str;rank_position:int;ranking_limitations:tuple;ranking_commitment:str;schema_version:str='rsi006-v1'
 def validate(self):
  need(self.eligibility_class=='INELIGIBLE' and self.priority_class=='REVIEW_ONLY','ELIGIBILITY');integer(self.rank_position);need(1<=self.rank_position<=8,'RANK');need(type(self.criterion_results) is tuple and len(self.criterion_results)==7,'CRITERIA')
  for row in self.criterion_results:need(type(row) is tuple and len(row)==2 and row[0] in CRITERIA and row[1] in ('NOT_QUALIFIED','MISSING','OBSERVED_REGRESSION','NO_OBSERVED_REGRESSION'),'CRITERION_RESULT')
  need(tuple(x[0] for x in self.criterion_results)==tuple(sorted(CRITERIA)),'ORDER');strings(self.ranking_limitations)
@dataclass(frozen=True)
class GovernancePolicy(Contract):
 policy_version:str;permitted_selection_operations:tuple;mandatory_gate_requirements:tuple;minimum_evidence_requirements:tuple;inherited_blocker_rules:str;prohibited_operations:tuple;resource_limits:int;required_approval_classes:tuple;commitment:str;schema_version:str='rsi006-v1'
 def validate(self):
  ident(self.policy_version);need(self.permitted_selection_operations==('ADVISORY_REVIEW',) and self.mandatory_gate_requirements==q.GATES,'POLICY');need(self.minimum_evidence_requirements==('ORIGINAL_SOURCE_REPLAY','NO_AUTHENTICITY_UPGRADE') and self.inherited_blocker_rules=='PRESERVE_ALL_BLOCKING','BLOCKERS');need(self.prohibited_operations==q.e.DENIED and self.required_approval_classes==('EXTERNAL_APPROVAL_NOT_IMPLEMENTED',),'AUTHORITY');integer(self.resource_limits);need(1<=self.resource_limits<=64,'BUDGET')
@dataclass(frozen=True)
class AuthorizationRecord(Contract):
 authorization_id:str;candidate_id:str;authorization_class:str;issuer_reference:str;authorization_scope:tuple;authorization_status:str;provenance_class:str;source_commitment:str;commitment:str;schema_version:str='rsi006-v1'
 def validate(self):
  need(self.authorization_class=='DESCRIPTIVE_EXTERNAL_CLAIM' and self.authorization_status=='NOT_QUALIFIED','AUTHORITY');ident(self.issuer_reference);need(self.issuer_reference not in ('SELF',self.candidate_id),'SELF_AUTHORIZATION');need(self.authorization_scope==('ADVISORY_REVIEW_ONLY',) and self.provenance_class in ('REPORTED_ONLY','UNAVAILABLE'),'SCOPE')
@dataclass(frozen=True)
class GovernanceState(Contract):
 state_version:str;sequence:int;previous_state_commitment:str;registered_candidates:tuple;evaluated_candidates:tuple;rejected_candidates:tuple;cumulative_resource_usage:int;policy_commitment:str;history:tuple;state_commitment:str;schema_version:str='rsi006-v1'
 def validate(self):
  need(self.state_version=='state-v1','STATE');integer(self.sequence);integer(self.cumulative_resource_usage)
  for x in (self.registered_candidates,self.evaluated_candidates,self.rejected_candidates):strings(x)
  need(self.registered_candidates==self.evaluated_candidates==self.rejected_candidates,'STATE');need(self.cumulative_resource_usage==len(self.registered_candidates)*2,'ACCOUNTING');need(type(self.history) is tuple and len(self.history)==self.sequence<=len(self.registered_candidates),'HISTORY')
  for x in self.history:hashcheck(x)
@dataclass(frozen=True)
class GovernanceVerdict(Contract):
 candidate_id:str;eligibility_status:str;ranking_status:str;evidence_qualification:str;gate_qualification:str;authorization_status:str;unresolved_findings:tuple;decision:str;decision_reasons:tuple;authorization_flags:tuple;commitment:str;schema_version:str='rsi006-v1'
 def validate(self):
  need(self.eligibility_status=='INELIGIBLE' and self.ranking_status=='ADVISORY_ONLY','STATUS');need(self.evidence_qualification=='NOT_INDEPENDENTLY_QUALIFIED' and self.gate_qualification in ('FAIL','NOT_QUALIFIED') and self.authorization_status=='NOT_AUTHORIZED','QUALIFICATION');need(self.unresolved_findings==BLOCKERS and self.decision in DECISIONS and self.decision!='ADVISORY_SELECTED','DECISION');strings(self.decision_reasons);need(type(self.authorization_flags) is tuple and len(self.authorization_flags)==7,'FLAGS')
  for pair,name in zip(self.authorization_flags,FLAGS):need(type(pair) is tuple and len(pair)==2 and pair[0]==name and pair[1] is False,'AUTHORITY')
