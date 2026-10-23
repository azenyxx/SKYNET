"""Pure comparisons. No candidate code, shell, process or network execution."""
from experiment_contracts import *
import improvement_proposal_engine as upstream

def initial(policy):
 check(policy,ExperimentPolicy)
 return make(ExperimentState,state_version='state-v1',sequence=0,previous_state_commitment='0'*64,registered_experiments=(),evaluated_experiments=(),rejected_experiments=(),cumulative_resource_usage=0,policy_commitment=policy.commitment,history=())
def evaluate(spec,environment,measurements,source_call,source_result,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
 for x,c in ((spec,ExperimentSpecification),(environment,ExperimentEnvironment),(policy,ExperimentPolicy),(previous,ExperimentState)):check(x,c)
 need(type(measurements) is tuple and len(measurements)<=16,'MEASUREMENTS')
 for m in measurements:check(m,ExperimentMeasurement)
 strings(tuple(m.measurement_id for m in measurements));strings(tuple(m.source_commitment for m in measurements))
 ordered=tuple(sorted(measurements,key=lambda x:x.measurement_id))
 need(approved_input==digest((spec,environment,ordered,source_call,source_result,policy)),'INPUT_PIN');need(expected_state==previous.state_commitment and policy.commitment==previous.policy_commitment,'STATE_PIN');integer(sequence);need(sequence==previous.sequence+1 and spec.experiment_id not in previous.registered_experiments,'REPLAY')
 cost=1+len(measurements);need(cost<=spec.resource_limits<=policy.resource_limits,'BUDGET')
 p.r.q.v.m.t.r.s.replay.learning.memory.guard(stop,now,deadline,policy.resource_limits-previous.cumulative_resource_usage,cost)
 need(type(source_call) is tuple and len(source_call)==8,'SOURCE_CALL');need(type(source_result) is tuple and len(source_result)==2,'SOURCE_RESULT')
 srcargs,srcresult,hid,pid,metric,direction,baseline,srcstate=source_call
 p.check(srcstate,p.ProposalState)
 actual=upstream.construct(*source_call,expected_state=srcstate.state_commitment,approved_input=p.digest((srcargs,srcresult,hid,pid,metric,direction,baseline)),sequence=srcstate.sequence+1,stop=stop,now=now,deadline=deadline)
 need(actual==source_result and spec.source_commitment==digest(source_result),'SOURCE_REPLAY')
 h,ev,prediction,proposal,deps,risk,pv=actual[1]
 need(spec.proposal_id==proposal.proposal_id and spec.hypothesis_id==h.hypothesis_id==proposal.hypothesis_id and spec.target_component==proposal.target_component and spec.target_version==proposal.target_version,'PROPOSAL_BINDING')
 definitions={x[0]:x[1:] for x in spec.target_metrics};need(metric in definitions and definitions[metric][1]==direction,'PREDICTION_BINDING')
 groups={};incompatible=False;contradicted=pv.decision=='CONTRADICTED'
 for m in ordered:
  need(m.experiment_id==spec.experiment_id and m.component_id==spec.target_component and m.metric_id in definitions,'MEASUREMENT_IDENTITY')
  need(m.subject_commitment==(spec.baseline_ref if m.subject_type=='BASELINE' else spec.candidate_ref),'SUBJECT_BINDING');need(m.component_version==(spec.target_version if m.subject_type=='BASELINE' else spec.candidate_version),'VERSION_BINDING')
  unit,direct,context=definitions[m.metric_id];incompatible|=(m.metric_unit!=unit or m.measurement_context!=context)
  contradicted|=m.provenance_class=='CONTRADICTED'
  groups.setdefault((m.metric_id,m.subject_type),[]).append(m)
 comparisons=[];changes=[];missing=False;ambiguous=False;unavailable=False
 for mid in sorted(definitions):
  left=groups.get((mid,'BASELINE'),[]);right=groups.get((mid,'CANDIDATE'),[])
  if not left or not right:missing=True;continue
  if len(left)!=1 or len(right)!=1:ambiguous=True;continue
  a,b=left[0],right[0];unavailable|=any(m.provenance_class=='UNAVAILABLE' or m.verification_status=='UNAVAILABLE' for m in (a,b))
  if incompatible:continue
  direct=definitions[mid][1];delta=b.metric_value-a.metric_value
  comparisons.append(make(ExperimentComparison,experiment_id=spec.experiment_id,baseline_measurement_id=a.measurement_id,candidate_measurement_id=b.measurement_id,metric_id=mid,metric_direction=direct,baseline_value=a.metric_value,candidate_value=b.metric_value,observed_delta=delta,comparability_status='COMPARABLE_DIAGNOSTIC'))
  changes.append(delta if direct=='HIGHER' else -delta)
 regression=any(x<0 for x in changes);improvement=any(x>0 for x in changes)
 blocked=spec.experiment_type not in policy.permitted_experiment_types or spec.experiment_type in ('INTERFACE_COMPATIBILITY_CHECK','EVIDENCE_QUALIFICATION') or pv.decision in ('RISK_BLOCKED','POLICY_BLOCKED','REJECTED') or bool(risk.security_risks or risk.authorization_risks)
 outcome='POLICY_BLOCKED' if blocked else 'NOT_COMPARABLE' if incompatible else 'REGRESSION_OBSERVED' if regression else 'INCONCLUSIVE' if contradicted or ambiguous or unavailable else 'EVIDENCE_REQUIRED' if missing else 'IMPROVEMENT_OBSERVED' if improvement else 'NO_MEASURABLE_CHANGE'
 reasons=['SUPPLIED_OBSERVATIONS_ONLY','NO_INDEPENDENT_PROVENANCE','NO_OS_SANDBOX','INHERITED_P1_OPEN']
 if regression:reasons.append('FALSIFIED_REGRESSION')
 if not improvement:reasons.append('NO_IMPROVEMENT_ESTABLISHED')
 if contradicted or ambiguous:reasons.append('CONTRADICTORY_OR_AMBIGUOUS_OBSERVATIONS')
 if missing:reasons.append('MISSING_REQUIRED_MEASUREMENTS')
 erisk=make(ExperimentRiskAssessment,experiment_id=spec.experiment_id,resource_risks=(),regression_risks=tuple(c.metric_id for c,g in zip(comparisons,changes) if g<0),security_risks=risk.security_risks,provenance_gaps=('INDEPENDENT_MEASUREMENT_AUTHENTICITY',),isolation_limitations=('NO_HOSTILE_CODE_EXECUTION','NO_OS_ISOLATION'),unresolved_blockers=BLOCKERS)
 verdict=make(ExperimentVerdict,experiment_id=spec.experiment_id,structural_validity=True,evidence_qualification='NOT_INDEPENDENTLY_QUALIFIED',environment_qualification='INTERFACE_ONLY',comparison_status='NOT_COMPARABLE' if incompatible else 'INCOMPLETE' if missing or ambiguous else 'COMPLETE',regression_status='OBSERVED' if regression else 'NOT_QUALIFIED' if missing or incompatible or ambiguous or unavailable else 'NOT_OBSERVED',observed_outcome=outcome,unresolved_findings=BLOCKERS,decision='ADVISORY_NOT_AUTHORIZED',decision_reasons=tuple(sorted(reasons)),authorization_flags=tuple((f,False) for f in FLAGS))
 ids=previous.registered_experiments+(spec.experiment_id,)
 state=make(ExperimentState,state_version='state-v1',sequence=sequence,previous_state_commitment=previous.state_commitment,registered_experiments=ids,evaluated_experiments=ids,rejected_experiments=previous.rejected_experiments+((spec.experiment_id,) if blocked else ()),cumulative_resource_usage=previous.cumulative_resource_usage+cost,policy_commitment=policy.commitment,history=previous.history+(digest((approved_input,tuple(comparisons),erisk,verdict)),))
 return state,tuple(comparisons),erisk,verdict
