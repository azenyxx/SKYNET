"""Bounded qualification contracts; commitments never establish authenticity."""
from dataclasses import dataclass,fields,make_dataclass
import versioning_contracts as v
need=v.need
FLAGS=v.FLAGS
STAGES=tuple('RSI-%03d'%i for i in range(1,8))
CAPS=('contracts','bottlenecks','hypotheses','comparisons','regression','governance','versioning','rollback','integration','autonomous_rsi')
FINDINGS=v.BLOCKERS+('RSI07-001','RSI07-002','RSI07-003','RSI07-004','RSI07-R1-001','RSI08-001','RSI08-002','RSI08-003')
def digest(x):return v.digest(('RSI008-v1',x))
class Contract:
 def __post_init__(self):
  need(self.schema_version=='rsi008-v1','VERSION')
  for f in fields(self):
   x=getattr(self,f.name)
   need(type(x) is f.type,'FIELD_TYPE')
   if f.name.endswith('_id') or f.name.endswith('_version'):v.ident(x)
   if f.name.endswith('_commitment'):v.hashcheck(x)
   if isinstance(x,(list,dict,set)):need(False,'MUTABLE')
  validate(self)
  need(self.commitment==digest((type(self).__name__,tuple((f.name,getattr(self,f.name)) for f in fields(self) if f.name!='commitment'))),'COMMITMENT')
def make(c,**kw):
 if c.__name__=='QualificationState':kw['state_commitment']=digest(('state-fields',kw['state_version'],kw['sequence'],kw['previous_state_commitment'],kw['assessed_stages'],kw['assessed_capabilities'],kw['unresolved_findings'],kw['cumulative_resource_usage']))
 values={f.name:kw.get(f.name,f.default) for f in fields(c) if f.name!='commitment'}
 return c(**values,commitment=digest((c.__name__,tuple(values.items()))))
def check(x,c):need(type(x) is c,'TYPE');x.__post_init__()
def rows(x):
 need(type(x) is tuple and len(x)<=64,'BOUND')
 for y in x:need(type(y) in (str,int,bool,tuple),'MEMBER_TYPE')
 def nested(v,d=0):
  need(d<=4,'MEMBER_DEPTH')
  if type(v) is tuple:
   need(len(v)<=64,'BOUND')
   for a in v:nested(a,d+1)
  else:need(type(v) in (str,int,bool),'MEMBER_TYPE')
 nested(x)
def validate(x):
 name=type(x).__name__
 for f in fields(x):
  value=getattr(x,f.name)
  if f.type is tuple:rows(value)
 if name=='StageQualificationRecord':
  need(x.stage_id in STAGES,'STAGE');need(x.reported_status in ('CLOSED_PARTIAL','UNKNOWN'),'STATUS');need(x.integration_class in ('FIXTURE_BASED_ONLY','NOT_TESTED'),'INTEGRATION');need(len(x.observed_test_results)==4,'COUNTS')
  for n in x.observed_test_results:v.integer(n)
 elif name=='QualificationEvidence':need(x.provenance_class=='SYNTHETIC_LOCAL' and x.verification_status=='NOT_INDEPENDENTLY_QUALIFIED','EVIDENCE_PROMOTION')
 elif name=='QualificationFinding':need(x.severity in ('P1','P2','UNKNOWN') and x.current_status=='OPEN' and x.inherited_flag is True,'FINDING')
 elif name=='CapabilityAssessment':need(x.qualification_status in ('FIXTURE_BASED_ONLY','BLOCKED','FAILED','NOT_INDEPENDENTLY_QUALIFIED'),'CAPABILITY_PROMOTION')
 elif name=='QualificationPolicy':
  need(x.mandatory_capabilities==CAPS and x.finding_rules=='PRESERVE_ALL_NONEXHAUSTIVE','POLICY');need(x.authorization_constraints==tuple((f,False) for f in FLAGS),'AUTHORITY');v.integer(x.resource_limits);need(1<=x.resource_limits<=64,'BUDGET')
 elif name=='QualificationState':
  need(x.state_commitment==digest(('state-fields',x.state_version,x.sequence,x.previous_state_commitment,x.assessed_stages,x.assessed_capabilities,x.unresolved_findings,x.cumulative_resource_usage)),'STATE_COMMITMENT')
  v.integer(x.sequence);v.integer(x.cumulative_resource_usage);need(x.sequence in (0,1) and x.cumulative_resource_usage==x.sequence*7,'ACCOUNTING');need(x.unresolved_findings==FINDINGS,'FINDINGS')
 elif name=='IntegratedQualificationVerdict':
  need(x.authorization_flags==tuple((f,False) for f in FLAGS),'AUTHORITY');need(x.unresolved_findings==FINDINGS,'FINDINGS');need(x.series_status in ('SERIES_CLOSED_PARTIAL','SERIES_BLOCKED','SERIES_FAILED'),'FALSE_FULL');need(x.evidence_qualification=='NOT_INDEPENDENTLY_QUALIFIED','EVIDENCE_PROMOTION')
 elif name=='IntegrationChainRecord':need(x.ordered_stage_ids==STAGES and x.integration_status=='FIXTURE_BASED_ONLY','CHAIN')
# Explicit schemas, frozen DTOs; arbitrary object fields are not accepted by bounded canonical encoding.
DEFINITIONS={
'StageQualificationRecord':'stage_id stage_version artifact_commitment reported_status observed_test_results:tuple integration_class evidence_refs:tuple qualification_limitations:tuple',
'IntegrationChainRecord':'chain_id ordered_stage_ids:tuple interface_bindings:tuple input_commitments:tuple output_commitments:tuple executed_paths:tuple fixture_dependencies:tuple integration_status',
'QualificationEvidence':'evidence_id source_stage source_artifact evidence_type provenance_class verification_status source_commitment limitations:tuple',
'QualificationFinding':'finding_id severity originating_stage affected_capabilities:tuple evidence_refs:tuple current_status closure_requirements:tuple inherited_flag:bool',
'CapabilityAssessment':'capability_id required_stages:tuple required_evidence:tuple observed_evidence:tuple qualification_status unresolved_blockers:tuple limitations:tuple',
'QualificationPolicy':'policy_version mandatory_capabilities:tuple evidence_requirements:tuple integration_requirements:tuple finding_rules authorization_constraints:tuple resource_limits:int prohibited_operations:tuple',
'QualificationState':'state_version sequence:int previous_state_commitment assessed_stages:tuple assessed_capabilities:tuple unresolved_findings:tuple cumulative_resource_usage:int state_commitment',
'IntegratedQualificationVerdict':'qualification_id stage_results:tuple integration_result capability_results:tuple evidence_qualification safety_status unresolved_findings:tuple series_status decision_reasons:tuple authorization_flags:tuple'}
for name,spec in DEFINITIONS.items():
 fs=[]
 for item in spec.split():
  a,_,b=item.partition(':');fs.append((a,{'tuple':tuple,'int':int,'bool':bool}.get(b,str)))
 globals()[name]=make_dataclass(name,fs+[('commitment',str),('schema_version',str,'rsi008-v1')],bases=(Contract,),frozen=True,namespace={'__module__':__name__})
