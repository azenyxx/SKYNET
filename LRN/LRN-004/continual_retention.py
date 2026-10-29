"""Read-only observations, integer metrics, interval-conservative comparisons."""
from retention_contracts import *
def initial(policy):
    obj(policy,RetentionPolicy)
    return make(RetentionState,processed_ids=(),consumed=0,remaining=policy.budget,sequence=0,previous_state_commitment='0'*64,policy_commitment=policy.commitment,history=(),provenance=())
def evaluate(baseline,evidence,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
    for v,c in ((baseline,RetentionBaseline),(evidence,AdaptationEvidence),(policy,RetentionPolicy),(previous,RetentionState)): obj(v,c)
    pin=digest((baseline,evidence,policy))
    need(approved_input==pin and expected_state==previous.commitment,'HOST_PIN')
    need(previous.policy_commitment==policy.commitment,'POLICY')
    need(previous.consumed+previous.remaining==policy.budget,'BUDGET_ESCALATION')
    integer(sequence); need(sequence==previous.sequence+1,'SEQUENCE')
    need(evidence.evaluation_id not in previous.processed_ids,'DUPLICATE')
    cost=1+len(baseline.snapshots)+len(evidence.snapshots)
    s.replay.learning.memory.guard(stop,now,deadline,previous.remaining,cost)
    need(evidence.proposal.estimated_cost<=policy.max_cost,'COST')
    b={x.metric_id:x for x in baseline.snapshots}; c={x.metric_id:x for x in evidence.snapshots}
    need(set(c)<=set(b),'INCOMPARABLE_COVERAGE')
    assessments=[]
    for key in sorted(b):
        x=b[key]; y=c.get(key)
        if y is None: status,reason='INSUFFICIENT_EVIDENCE','MISSING_MEASUREMENT'
        else:
            need((x.unit,x.direction,x.population)==(y.unit,y.direction,y.population),'INCOMPARABLE')
            need(x.snapshot_id!=y.snapshot_id and x.commitment!=y.commitment,'REPEATED_EVIDENCE')
            if not baseline.provenance or not x.provenance or x.quality!='DIAGNOSTIC': status,reason='BASELINE_UNQUALIFIED','BASELINE_PROVENANCE'
            elif not evidence.provenance or not y.provenance or y.quality!='DIAGNOSTIC': status,reason='INSUFFICIENT_EVIDENCE','CANDIDATE_PROVENANCE'
            else:
                loss=(x.value-y.value) if x.direction=='HIGHER' else (y.value-x.value)
                uncertainty=x.uncertainty+y.uncertainty
                if loss-uncertainty>policy.tolerance: status,reason='REGRESSION_DETECTED','INTERVAL_REGRESSION'
                elif loss+uncertainty<=policy.tolerance: status,reason='RETENTION_PRESERVED','DIAGNOSTIC_COMPARISON_ONLY'
                else: status,reason='INSUFFICIENT_EVIDENCE','UNCERTAINTY_OVERLAP'
        assessments.append(make(RegressionAssessment,metric_id=key,status=status,reasons=(reason,),provenance=x.provenance))
    statuses={x.status for x in assessments}
    if not b: status='BASELINE_UNQUALIFIED'
    elif evidence.proposal.status in ('BLOCKED','REJECTED','NOT_QUALIFIED') or not evidence.source.classifications: status='NOT_QUALIFIED'
    else: status=next(x for x in ('REGRESSION_DETECTED','BASELINE_UNQUALIFIED','INSUFFICIENT_EVIDENCE','RETENTION_PRESERVED') if x in statuses)
    result=make(RetentionEvaluation,evaluation_id=evidence.evaluation_id,input_commitment=pin,assessments=tuple(assessments),status=status,source_diversity=evidence.source.source_diversity,estimated_cost=evidence.proposal.estimated_cost,blockers=BLOCKERS,provenance=evidence.provenance)
    state=make(RetentionState,processed_ids=previous.processed_ids+(evidence.evaluation_id,),consumed=previous.consumed+cost,remaining=previous.remaining-cost,sequence=sequence,previous_state_commitment=previous.commitment,policy_commitment=policy.commitment,history=previous.history+(result.commitment,),provenance=previous.provenance)
    return state,result,make(RetentionVerdict,status=status,provenance=evidence.provenance)
