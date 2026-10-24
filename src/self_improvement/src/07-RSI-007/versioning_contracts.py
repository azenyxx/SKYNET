"""Immutable snapshot assessment contracts; no restoration authority."""
from dataclasses import dataclass,fields
import governance_contracts as g
need,ident,integer,refs,hashcheck=g.need,g.ident,g.integer,g.refs,g.hashcheck
FLAGS=g.FLAGS
BLOCKERS=g.BLOCKERS+('RSI06-001','RSI06-002','RSI06-003')
GATES=('SOURCE_INTEGRITY','TARGET_INTEGRITY','VERSION_CONTINUITY','DEPENDENCY_COMPATIBILITY','INTERFACE_COMPATIBILITY','REGRESSION_STATUS','GOVERNANCE_ELIGIBILITY','ROLLBACK_READINESS','AUTHORIZATION_BOUNDARY','INHERITED_BLOCKERS')
SIM=('SIMULATION_PASSED','SIMULATION_FAILED','RESTORATION_EVIDENCE_REQUIRED','DEPENDENCY_BLOCKED','STATE_INCOMPATIBLE','NOT_QUALIFIED','POLICY_BLOCKED')
SEALS={'VersionSnapshot':'snapshot_commitment','VersionTransition':'transition_commitment','VersionDependency':'dependency_commitment','RollbackPlan':'plan_commitment','VersioningState':'state_commitment'}
def digest(x):
 """R1 typed Merkle encoding: all fields included; bounded depth/nodes/bytes.
 No nested seal is accepted as authority. Original replay validates subobjects.
 """
 import hashlib,json
 from dataclasses import is_dataclass
 from fractions import Fraction
 count=[0];size=[0]
 def walk(v,depth=0):
  need(depth<=32,'R1_SERIALIZATION_DEPTH');count[0]+=1;need(count[0]<=20000,'R1_SERIALIZATION_SIZE')
  if is_dataclass(v) and not isinstance(v,type):
   node=['dataclass',type(v).__module__,type(v).__qualname__,[[f.name,walk(getattr(v,f.name),depth+1)] for f in fields(v)]]
  elif type(v) is tuple:
   need(len(v)<=256,'R1_SERIALIZATION_SIZE');node=['tuple',[walk(y,depth+1) for y in v]]
  elif type(v) is dict:
   need(len(v)<=64 and all(type(k) is str for k in v),'R1_SERIALIZATION_KEYS');node=['dict',[[k,walk(v[k],depth+1)] for k in sorted(v)]]
  elif type(v) is Fraction:
   need(abs(v.numerator)<=10**12 and v.denominator<=10**12,'R1_SERIALIZATION_NUMBER');node=['fraction',v.numerator,v.denominator]
  elif type(v) is str:
   n=len(v.encode('utf-8'));need(n<=4096,'R1_SERIALIZATION_SIZE');size[0]+=n;need(size[0]<=1048576,'R1_SERIALIZATION_SIZE');node=['str',v]
  elif type(v) is bool:node=['bool',v]
  elif type(v) is int:
   need(abs(v)<=10**12,'R1_SERIALIZATION_NUMBER');node=['int',v]
  elif v is None:node=['none']
  else:need(False,'R1_SERIALIZATION_TYPE')
  return hashlib.sha256(b'SKYNET:RSI007:R1:node:v1\0'+json.dumps(node,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
 return hashlib.sha256(b'SKYNET:RSI007:R1:root:v1\0'+walk(x).encode()).hexdigest()
def seal(c):return SEALS.get(c.__name__,'commitment')
def make(c,**kw):
 k=seal(c);return c(**kw,**{k:digest((c.__name__,tuple((f.name,kw.get(f.name,f.default)) for f in fields(c) if f.name!=k)))})
def check(x,c):need(type(x) is c,'TYPE');x.__post_init__()
def strings(x):refs(x);need(len(x)<=48,'BOUND')
def hashes(x):strings(x);[hashcheck(h) for h in x]
class Contract:
 def __post_init__(self):
  need(self.schema_version=='rsi007-v1','VERSION')
  for f in fields(self):
   v=getattr(self,f.name)
   if f.name.endswith('_id'):ident(v)
   if f.name.endswith('_commitment'):hashcheck(v)
  self.validate();k=seal(type(self));hashcheck(getattr(self,k));need(getattr(self,k)==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!=k))),'COMMITMENT')
@dataclass(frozen=True)
class VersionSnapshot(Contract):
 snapshot_id:str;component_id:str;component_version:str;source_commitment:str;interface_commitments:tuple;dependency_commitments:tuple;configuration_commitment:str;provenance_class:str;snapshot_commitment:str;schema_version:str='rsi007-v1'
 def validate(self):ident(self.component_version);hashes(self.interface_commitments);hashes(self.dependency_commitments);g.q.e.p.s.provenance(self.provenance_class)
@dataclass(frozen=True)
class VersionTransition(Contract):
 transition_id:str;proposal_id:str;candidate_id:str;source_snapshot_id:str;target_snapshot_id:str;governance_verdict_ref:str;evaluation_verdict_ref:str;compatibility_requirements:tuple;transition_commitment:str;schema_version:str='rsi007-v1'
 def validate(self):
  need(self.source_snapshot_id!=self.target_snapshot_id,'IDENTITY');hashcheck(self.governance_verdict_ref);hashcheck(self.evaluation_verdict_ref);need(self.compatibility_requirements==('EXACT_DECLARED_INTERFACES','EXACT_DECLARED_DEPENDENCIES'),'REQUIREMENTS')
@dataclass(frozen=True)
class VersionDependency(Contract):
 component_id:str;component_version:str;required_dependencies:tuple;interface_constraints:tuple;compatibility_status:str;unresolved_dependencies:tuple;dependency_commitment:str;schema_version:str='rsi007-v1'
 def validate(self):ident(self.component_version);hashes(self.required_dependencies);hashes(self.interface_constraints);strings(self.unresolved_dependencies);need(self.compatibility_status=='DECLARED_NOT_QUALIFIED','COMPATIBILITY')
@dataclass(frozen=True)
class RollbackPlan(Contract):
 rollback_id:str;transition_id:str;target_snapshot_id:str;restoration_requirements:tuple;state_compatibility_requirements:tuple;dependency_requirements:tuple;required_evidence:tuple;prohibited_effects:tuple;plan_commitment:str;schema_version:str='rsi007-v1'
 def validate(self):
  need(self.restoration_requirements==('EXACT_SOURCE_SNAPSHOT',) and self.state_compatibility_requirements==('IMMUTABLE_COMMITMENT_EQUALITY_ONLY',),'RESTORATION');hashes(self.dependency_requirements);need(self.required_evidence==('HOST_PINNED_RESTORATION_SNAPSHOT',) and self.prohibited_effects==g.q.e.DENIED+('ACTUAL_ROLLBACK',),'POLICY')
@dataclass(frozen=True)
class RollbackSimulation(Contract):
 simulation_id:str;rollback_id:str;initial_state_commitment:str;expected_state_commitment:str;observed_simulated_commitment:str;dependency_results:tuple;invariant_results:tuple;simulation_status:str;limitations:tuple;commitment:str;schema_version:str='rsi007-v1'
 def validate(self):
  for rows in (self.dependency_results,self.invariant_results):
   need(type(rows) is tuple and len(rows)<=8,'RESULTS')
   for row in rows:need(type(row) is tuple and len(row)==2 and row[1] in ('PASS','FAIL','NOT_QUALIFIED'),'RESULT');ident(row[0])
  need(self.simulation_status in SIM,'STATUS');strings(self.limitations)
  if self.simulation_status=='SIMULATION_PASSED':need(self.expected_state_commitment==self.observed_simulated_commitment and all(v=='PASS' for k,v in self.dependency_results+self.invariant_results),'FALSE_SUCCESS')
@dataclass(frozen=True)
class SafetyValidationPolicy(Contract):
 policy_version:str;permitted_validation_operations:tuple;mandatory_safety_gates:tuple;versioning_requirements:tuple;rollback_requirements:tuple;evidence_requirements:tuple;inherited_blocker_rules:str;resource_limits:int;prohibited_operations:tuple;commitment:str;schema_version:str='rsi007-v1'
 def validate(self):
  ident(self.policy_version);need(self.permitted_validation_operations==('SNAPSHOT_COMPARISON','DECLARATIVE_ROLLBACK') and self.mandatory_safety_gates==GATES,'OPERATIONS');need(self.versioning_requirements==('EXACT_SOURCE_BINDING',) and self.rollback_requirements==('NO_ACTUAL_RESTORATION',) and self.evidence_requirements==('ORIGINAL_GOVERNANCE_REPLAY',) and self.inherited_blocker_rules=='PRESERVE_ALL','POLICY');integer(self.resource_limits);need(1<=self.resource_limits<=64,'BUDGET');need(self.prohibited_operations==g.q.e.DENIED+('ACTUAL_ROLLBACK',),'AUTHORITY')
@dataclass(frozen=True)
class VersioningState(Contract):
 state_version:str;sequence:int;previous_state_commitment:str;registered_snapshots:tuple;evaluated_transitions:tuple;simulated_rollbacks:tuple;cumulative_resource_usage:int;policy_commitment:str;history:tuple;state_commitment:str;schema_version:str='rsi007-v1'
 def validate(self):
  need(self.state_version=='state-v1','STATE');integer(self.sequence);integer(self.cumulative_resource_usage)
  for x in (self.registered_snapshots,self.evaluated_transitions,self.simulated_rollbacks):strings(x)
  need(type(self.history) is tuple and len(self.history)==self.sequence==len(self.evaluated_transitions)==len(self.simulated_rollbacks) and self.cumulative_resource_usage==self.sequence*3,'ACCOUNTING')
  for h in self.history:hashcheck(h)
@dataclass(frozen=True)
class SafetyValidationVerdict(Contract):
 transition_id:str;structural_validity:bool;provenance_qualification:str;compatibility_status:str;governance_status:str;rollback_status:str;safety_gate_results:tuple;unresolved_findings:tuple;decision:str;decision_reasons:tuple;authorization_flags:tuple;commitment:str;schema_version:str='rsi007-v1'
 def validate(self):
  need(self.structural_validity is True and self.provenance_qualification=='NOT_INDEPENDENTLY_QUALIFIED' and self.compatibility_status=='NOT_QUALIFIED' and self.governance_status=='NO_ELIGIBLE_CANDIDATE','QUALIFICATION');need(self.rollback_status in SIM and self.decision=='GOVERNANCE_BLOCKED' and self.unresolved_findings==BLOCKERS,'DECISION');strings(self.decision_reasons);need(type(self.safety_gate_results) is tuple and len(self.safety_gate_results)==10,'GATES')
  for row in self.safety_gate_results:need(type(row) is tuple and len(row)==2 and row[0] in GATES and row[1] in ('PASS','FAIL','INCONCLUSIVE','NOT_QUALIFIED','POLICY_BLOCKED'),'GATE')
  need(tuple(k for k,v in self.safety_gate_results)==tuple(sorted(GATES)),'ORDER');need(type(self.authorization_flags) is tuple and len(self.authorization_flags)==7,'FLAGS')
  for pair,name in zip(self.authorization_flags,FLAGS):need(type(pair) is tuple and len(pair)==2 and pair[0]==name and pair[1] is False,'AUTHORITY')
