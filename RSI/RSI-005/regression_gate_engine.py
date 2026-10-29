"""Advisory gates over replayed original experiment results."""
from comparative_evaluation_contracts import *
import sandboxed_experimentation as upstream

def initial(policy):
 check(policy,EvaluationPolicy)
 return make(EvaluationState,state_version='state-v1',sequence=0,previous_state_commitment='0'*64,evaluated_proposals=(),rejected_evaluations=(),cumulative_resource_usage=0,policy_commitment=policy.commitment,evaluation_ids=(),history=())
def evaluate(spec,thresholds,gates,source_call,source_result,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
 for x,c in ((spec,EvaluationSpecification),(policy,EvaluationPolicy),(previous,EvaluationState)):check(x,c)
 need(type(thresholds) is tuple and 1<=len(thresholds)<=8 and type(gates) is tuple and len(gates)==8,'BOUNDS')
 for t in thresholds:check(t,RegressionThreshold)
 for g in gates:check(g,RegressionGate)
 strings(tuple(t.metric_id for t in thresholds));strings(tuple(g.gate_id for g in gates));strings(tuple(g.gate_type for g in gates))
 ts=tuple(sorted(thresholds,key=lambda t:t.metric_id));gs=tuple(sorted(gates,key=lambda g:g.gate_id))
 need(expected_state==previous.state_commitment and previous.policy_commitment==policy.commitment,'STATE_PIN');need(approved_input==digest((spec,ts,gs,source_call,source_result,policy)),'INPUT_PIN');integer(sequence);need(sequence==previous.sequence+1 and spec.evaluation_id not in previous.evaluation_ids and spec.proposal_id not in previous.evaluated_proposals,'REPLAY')
 cost=1+len(ts)+len(gs);e.p.r.q.v.m.t.r.s.replay.learning.memory.guard(stop,now,deadline,policy.resource_limits-previous.cumulative_resource_usage,cost)
 need(spec.evaluation_policy_version==policy.policy_version and set(g.gate_type for g in gs)==set(policy.mandatory_gates) and set(spec.required_gate_ids)==set(g.gate_id for g in gs),'POLICY_BINDING')
 need(type(source_call) is tuple and len(source_call)==7 and type(source_result) is tuple and len(source_result)==4,'SOURCE')
 xs,env,measurements,pcall,presult,xpolicy,xstate=source_call
 e.check(xs,e.ExperimentSpecification);e.check(xstate,e.ExperimentState)
 need(spec.proposal_id==xs.proposal_id and spec.experiment_id==xs.experiment_id and spec.baseline_commitment==xs.baseline_ref and spec.candidate_commitment==xs.candidate_ref and spec.source_commitment==digest(source_result),'SOURCE_BINDING')
 definitions={row[0]:row[1:] for row in xs.target_metrics};need(set(spec.required_metric_ids)==set(definitions)==set(t.metric_id for t in ts),'METRIC_COVERAGE')
 for t in ts:need(t.threshold_unit==definitions[t.metric_id][0],'THRESHOLD_UNIT')
 for g in gs:need(set(g.required_metrics)==set(definitions) and set(g.threshold_refs)==set(t.commitment for t in ts),'GATE_COVERAGE')
 ordered=tuple(sorted(measurements,key=lambda m:m.measurement_id))
 actual=upstream.evaluate(*source_call,expected_state=xstate.state_commitment,approved_input=e.digest((xs,env,ordered,pcall,presult,xpolicy)),sequence=xstate.sequence+1,stop=stop,now=now,deadline=deadline)
 need(actual==source_result,'SOURCE_REPLAY')
 xv=actual[3];comparisons=actual[1];byid={m.measurement_id:m for m in measurements};metrics=[];results=[];contradicted=any(m.provenance_class=='CONTRADICTED' for m in measurements) or 'CONTRADICTORY_OR_AMBIGUOUS_OBSERVATIONS' in xv.decision_reasons
 usable=xv.comparison_status=='COMPLETE' and not contradicted and not any(m.verification_status=='UNAVAILABLE' or m.provenance_class=='UNAVAILABLE' for m in measurements)
 thresholds_by_id={t.metric_id:t for t in ts}
 for c in comparisons:
  e.check(c,e.ExperimentComparison);a=byid[c.baseline_measurement_id];b=byid[c.candidate_measurement_id];unit,direction,context=definitions[c.metric_id];need(c.metric_direction==direction,'DIRECTION')
  metrics.append(make(EvaluationMetric,metric_id=c.metric_id,baseline_measurement_ref=a.measurement_id,candidate_measurement_ref=b.measurement_id,unit=unit,optimization_direction=direction,baseline_value=c.baseline_value,candidate_value=c.candidate_value,comparison_context=context,provenance_class='CONTRADICTED' if contradicted else 'STRUCTURALLY_BOUND',verification_status='SUPPLIED_DIAGNOSTIC'))
  gain=c.observed_delta if direction=='HIGHER' else -c.observed_delta;t=thresholds_by_id[c.metric_id]
  results.append((c.metric_id,gain,'FAIL' if gain < -t.maximum_allowed_regression else 'PASS' if usable else 'NOT_QUALIFIED','FAIL' if gain<t.minimum_required_improvement else 'PASS' if usable else 'NOT_QUALIFIED'))
 complete=usable and set(c.metric_id for c in comparisons)==set(definitions)
 regression=any(row[1]<0 for row in results);failure=any(row[2]=='FAIL' or row[3]=='FAIL' for row in results)
 gate_results=[]
 for g in sorted(gs,key=lambda g:g.gate_type):
  if g.gate_type in ('METRIC_REGRESSION','PERFORMANCE_ACCEPTANCE'):
   idx=2 if g.gate_type=='METRIC_REGRESSION' else 3;status='FAIL' if any(row[idx]=='FAIL' for row in results) else 'PASS' if complete else 'NOT_QUALIFIED'
  elif g.gate_type=='INHERITED_BLOCKERS':status='FAIL'
  elif g.gate_type=='SAFETY_BOUNDARY' and xv.observed_outcome=='POLICY_BLOCKED':status='POLICY_BLOCKED'
  else:status='NOT_QUALIFIED'
  gate_results.append((g.gate_type,status))
 decision='POLICY_BLOCKED' if xv.observed_outcome=='POLICY_BLOCKED' else 'NOT_COMPARABLE' if xv.comparison_status=='NOT_COMPARABLE' else 'REGRESSION_DETECTED' if regression else 'REJECTED' if failure else 'EVIDENCE_REQUIRED' if not complete else 'INTEGRATION_NOT_QUALIFIED'
 evidence=make(ComparativeEvidence,evidence_id=spec.evaluation_id,evaluation_id=spec.evaluation_id,source_stage='RSI-004',source_artifact='experiment-result',evidence_type='SUPPLIED_OBSERVATIONS',provenance_class='CONTRADICTED' if contradicted else 'STRUCTURALLY_BOUND',verification_status='NOT_INDEPENDENTLY_QUALIFIED',source_commitment=digest(source_result),limitations=('INDEPENDENT_PROVENANCE_UNAVAILABLE','ORIGINAL_CLASSIFICATIONS_RETAINED_IN_SOURCE'))
 verdict=make(EvaluationVerdict,evaluation_id=spec.evaluation_id,proposal_id=spec.proposal_id,metric_results=tuple(sorted(results)),gate_results=tuple(gate_results),regression_status='OBSERVED' if regression else 'NOT_OBSERVED' if complete else 'NOT_QUALIFIED',evidence_qualification='NOT_INDEPENDENTLY_QUALIFIED',compatibility_status='NOT_QUALIFIED',safety_status='NOT_QUALIFIED',unresolved_findings=BLOCKERS,decision=decision,decision_reasons=('INHERITED_P1_OPEN','LOCAL_DIAGNOSTIC_ONLY','UNSUPPORTED_GATES_NOT_QUALIFIED','NO_ADOPTION_AUTHORITY'),authorization_flags=tuple((f,False) for f in FLAGS))
 state=make(EvaluationState,state_version='state-v1',sequence=sequence,previous_state_commitment=previous.state_commitment,evaluated_proposals=previous.evaluated_proposals+(spec.proposal_id,),rejected_evaluations=previous.rejected_evaluations+((spec.evaluation_id,) if decision in ('REGRESSION_DETECTED','REJECTED','POLICY_BLOCKED') else ()),cumulative_resource_usage=previous.cumulative_resource_usage+cost,policy_commitment=policy.commitment,evaluation_ids=previous.evaluation_ids+(spec.evaluation_id,),history=previous.history+(digest((approved_input,verdict)),))
 return state,tuple(metrics),evidence,verdict
