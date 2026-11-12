"""Fail-closed advisory governance over real original gate replay."""
from governance_contracts import *
import regression_gate_engine as upstream

def initial(policy):
 check(policy,GovernancePolicy)
 return make(GovernanceState,state_version='state-v1',sequence=0,previous_state_commitment='0'*64,registered_candidates=(),evaluated_candidates=(),rejected_candidates=(),cumulative_resource_usage=0,policy_commitment=policy.commitment,history=())
def select(entries,criteria,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
 check(policy,GovernancePolicy);check(previous,GovernanceState)
 need(type(entries) is tuple and 1<=len(entries)<=8 and type(criteria) is tuple and len(criteria)==7,'BOUNDS')
 for c in criteria:check(c,SelectionCriterion)
 strings(tuple(c.criterion_id for c in criteria));need(set(c.criterion_type for c in criteria)==set(CRITERIA) and all(c.policy_source==policy.policy_version for c in criteria),'CRITERIA')
 for item in entries:
  need(type(item) is tuple and len(item)==4,'ENTRY');check(item[0],SelectionCandidate)
  need(type(item[3]) is tuple and len(item[3])<=4,'AUTH_RECORDS')
  for auth in item[3]:check(auth,AuthorizationRecord);need(auth.candidate_id==item[0].candidate_id and auth.issuer_reference not in (item[0].proposal_id,item[0].target_component),'SELF_AUTHORIZATION')
  strings(tuple(a.authorization_id for a in item[3]))
 strings(tuple(x[0].candidate_id for x in entries));strings(tuple(x[0].proposal_id for x in entries));strings(tuple(x[0].evaluation_commitment for x in entries))
 ordered=tuple(sorted(entries,key=lambda x:x[0].candidate_id));cs=tuple(sorted(criteria,key=lambda c:c.criterion_id))
 need(approved_input==digest((ordered,cs,policy)) and expected_state==previous.state_commitment and previous.policy_commitment==policy.commitment,'HOST_PIN');integer(sequence);need(sequence==previous.sequence+1 and not set(x[0].candidate_id for x in entries)&set(previous.registered_candidates),'REPLAY')
 q.e.p.r.q.v.m.t.r.s.replay.learning.memory.guard(stop,now,deadline,policy.resource_limits-previous.cumulative_resource_usage,len(entries)*2)
 assessed=[];sources=[]
 for candidate,call,result,auths in ordered:
  need(type(call) is tuple and len(call)==7 and type(result) is tuple and len(result)==4,'SOURCE')
  spec,thresholds,gates,xcall,xresult,xpolicy,xstate=call
  q.check(spec,q.EvaluationSpecification);q.check(result[3],q.EvaluationVerdict);q.check(xstate,q.EvaluationState)
  actual=upstream.evaluate(*call,expected_state=xstate.state_commitment,approved_input=q.digest((spec,tuple(sorted(thresholds,key=lambda t:t.metric_id)),tuple(sorted(gates,key=lambda g:g.gate_id)),xcall,xresult,xpolicy)),sequence=xstate.sequence+1,stop=stop,now=now,deadline=deadline)
  need(actual==result and candidate.evaluation_commitment==digest(result),'EVALUATION_BINDING')
  proposal=xcall[4][1][3]
  q.e.p.check(proposal,q.e.p.ImprovementProposal)
  need(candidate.proposal_id==spec.proposal_id==proposal.proposal_id and candidate.evaluation_id==spec.evaluation_id and candidate.proposal_commitment==proposal.commitment and candidate.target_component==proposal.target_component and candidate.target_version==proposal.target_version,'PROPOSAL_BINDING')
  need(candidate.evidence_refs==(result[2].evidence_id,),'EVIDENCE_BINDING');sources.append(result[2].source_commitment)
  v=result[3];need(tuple(k for k,status in v.gate_results)==tuple(sorted(policy.mandatory_gate_requirements)),'MANDATORY_GATES')
  failed=any(status in ('FAIL','POLICY_BLOCKED') for k,status in v.gate_results)
  decision='POLICY_BLOCKED' if v.decision=='POLICY_BLOCKED' else 'RISK_BLOCKED' if v.decision=='REGRESSION_DETECTED' else 'REQUIRES_EVIDENCE' if v.decision=='EVIDENCE_REQUIRED' else 'INTEGRATION_NOT_QUALIFIED' if v.decision=='INTEGRATION_NOT_QUALIFIED' else 'GATE_BLOCKED' if failed else 'REJECTED'
  assessment=make(EligibilityAssessment,candidate_id=candidate.candidate_id,structural_status='VALID',evidence_status=v.evidence_qualification,mandatory_gate_status='FAIL' if failed else 'NOT_QUALIFIED',regression_status=v.regression_status,policy_status='BLOCKED' if decision=='POLICY_BLOCKED' else 'ADVISORY_ONLY',unresolved_blockers=BLOCKERS,eligibility_decision=decision,decision_reasons=('UPSTREAM_'+v.decision,'INHERITED_P1_OPEN','NO_VERIFIED_APPROVAL'))
  assessed.append(assessment)
 strings(tuple(sources))
 # Sorting is diagnostic review triage only. No unmeasured gain/cost is scored.
 ordered_assessments=tuple(sorted(assessed,key=lambda a:(a.regression_status=='OBSERVED',a.eligibility_decision=='POLICY_BLOCKED',a.candidate_id)))
 rankings=[];verdicts=[]
 for pos,a in enumerate(ordered_assessments,1):
  cr=tuple((kind,('OBSERVED_REGRESSION' if a.regression_status=='OBSERVED' else 'NO_OBSERVED_REGRESSION' if a.regression_status=='NOT_OBSERVED' else 'NOT_QUALIFIED') if kind=='REGRESSION_RISK' else 'MISSING' if kind in ('EXPECTED_IMPACT','RESOURCE_COST','IMPLEMENTATION_COMPLEXITY') else 'NOT_QUALIFIED') for kind in sorted(CRITERIA))
  rankings.append(make(CandidateRanking,candidate_id=a.candidate_id,eligibility_class='INELIGIBLE',criterion_results=cr,priority_class='REVIEW_ONLY',rank_position=pos,ranking_limitations=('NO_MEASURED_IMPACT_OR_COST','NO_AUTHORITY','ALL_CANDIDATES_UNQUALIFIED')))
  verdicts.append(make(GovernanceVerdict,candidate_id=a.candidate_id,eligibility_status='INELIGIBLE',ranking_status='ADVISORY_ONLY',evidence_qualification=a.evidence_status,gate_qualification=a.mandatory_gate_status,authorization_status='NOT_AUTHORIZED',unresolved_findings=BLOCKERS,decision=a.eligibility_decision,decision_reasons=a.decision_reasons,authorization_flags=tuple((f,False) for f in FLAGS)))
 ids=previous.registered_candidates+tuple(x[0].candidate_id for x in ordered)
 state=make(GovernanceState,state_version='state-v1',sequence=sequence,previous_state_commitment=previous.state_commitment,registered_candidates=ids,evaluated_candidates=ids,rejected_candidates=ids,cumulative_resource_usage=previous.cumulative_resource_usage+len(entries)*2,policy_commitment=policy.commitment,history=previous.history+(digest((approved_input,tuple(rankings),tuple(verdicts))),))
 return state,tuple(sorted(assessed,key=lambda a:a.candidate_id)),tuple(rankings),tuple(verdicts),'NO_ELIGIBLE_CANDIDATE'
