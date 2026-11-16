"""Conservative interval comparison. Costs never establish performance."""
from fractions import Fraction
from meta_learning_contracts import *
def initial(policy):
    check(policy,MetaLearningPolicy)
    return make(MetaLearningState,processed_ids=(),consumed=0,remaining=policy.budget,sequence=0,previous_state_commitment='0'*64,policy_commitment=policy.commitment,history=(),provenance=())
def evaluate(request_id,context,entries,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
    ident(request_id)
    for v,c in ((context,MetaLearningContext),(policy,MetaLearningPolicy),(previous,MetaLearningState)): check(v,c)
    need(type(entries) is tuple and 2<=len(entries)<=8,'CANDIDATE_BOUND')
    need(expected_state==previous.commitment and approved_input==digest((request_id,context,entries,policy)),'HOST_PIN')
    need(previous.policy_commitment==policy.commitment and previous.consumed+previous.remaining==policy.budget,'BUDGET')
    integer(sequence); need(sequence==previous.sequence+1 and request_id not in previous.processed_ids,'REPLAY')
    t.r.s.replay.learning.memory.guard(stop,now,deadline,previous.remaining,len(entries))
    ids=[]; observations=[]; rows=[]
    for pair in entries:
        need(type(pair) is tuple and len(pair)==2,'PAIR'); h,p=pair; check(h,StrategyHistory); check(p,StrategyPerformanceEvidence)
        need(p.history_commitment==h.commitment and p.context_commitment==context.commitment,'PERFORMANCE_BINDING')
        ids.append(h.strategy_id); observations.extend(x.snapshot_id for x in p.observations)
        reasons=['INDEPENDENT_PROVENANCE_NOT_ESTABLISHED']; status='COMPARABLE_NO_WINNER'; interval=None
        target=h.target
        if (target.domain_id,target.task_category,target.metric_id,target.unit,target.direction)!=(context.target_id,context.task_category,context.metric_id,context.unit,context.direction): status='INCOMPATIBLE'; reasons.append('CONTEXT_MISMATCH')
        for x in p.observations:
            need((x.metric_id,x.unit,x.direction,x.population)==(context.metric_id,context.unit,context.direction,context.population),'INCOMPARABLE_MEASUREMENT')
        if h.assessment.status=='INCOMPATIBLE' or h.candidate.status=='REJECTED': status='INCOMPATIBLE'; reasons.append('PREDECESSOR_INCOMPATIBLE')
        elif h.candidate.status=='NEGATIVE_TRANSFER_RISK' or any(a.status=='REGRESSION_DETECTED' for a in h.evidence.retention.assessments) or any(o!='COMPLETED' for o in h.evidence.adaptation.source.outcomes): status='REGRESSION_RISK'; reasons.append('SOURCE_FAILURE_OR_REGRESSION_RISK')
        elif status!='INCOMPATIBLE':
            if h.evidence.adaptation.proposal.estimated_cost>policy.max_declared_cost: status='NOT_QUALIFIED'; reasons.append('EXCESSIVE_DECLARED_COST')
            elif not h.provenance or not context.provenance or not p.provenance or not p.observations or any(not x.provenance or x.quality!='DIAGNOSTIC' for x in p.observations): status='INSUFFICIENT_EVIDENCE'; reasons.append('MISSING_MEASUREMENTS_OR_PROVENANCE')
            elif h.evidence.retention.status!='RETENTION_PRESERVED': status='INSUFFICIENT_EVIDENCE'; reasons.append('RETENTION_UNQUALIFIED')
            else:
                n=len(p.observations); low=sum(x.value-x.uncertainty for x in p.observations); high=sum(x.value+x.uncertainty for x in p.observations)
                interval=(Fraction(low,n),Fraction(high,n)) if context.direction=='HIGHER' else (Fraction(-high,n),Fraction(-low,n))
        rows.append([h,p,status,tuple(reasons),interval])
    refs(tuple(ids)); refs(tuple(observations))
    eligible=[x for x in rows if x[4] is not None]
    if len(eligible)>=2:
        for row in eligible:
            if all(row[4][0]>other[4][1] for other in eligible if other is not row): row[2]='PREFERRED_FOR_VALIDATION'
    elif eligible: eligible[0][2]='INSUFFICIENT_EVIDENCE'
    rank={'PREFERRED_FOR_VALIDATION':0,'COMPARABLE_NO_WINNER':1,'INSUFFICIENT_EVIDENCE':2,'NOT_QUALIFIED':3,'REGRESSION_RISK':4,'INCOMPATIBLE':5}
    assessments=[]; proposals=[]
    for h,p,status,reasons,interval in sorted(rows,key=lambda x:(rank[x[2]],x[0].strategy_id)):
        assessments.append(make(MetaStrategyAssessment,strategy_id=h.strategy_id,status=status,reasons=reasons,history_commitment=h.commitment,performance_commitment=p.commitment,provenance=p.provenance))
        if status in ('PREFERRED_FOR_VALIDATION','COMPARABLE_NO_WINNER'):
            proposals.append(make(MetaAdaptationProposal,strategy_id=h.strategy_id,existing_policy_commitment=policy.existing_policy_commitment,adjustment=policy.proposal_kind,supporting_commitments=(h.commitment,p.commitment),expected_cost=h.evidence.adaptation.proposal.estimated_cost,uncertainty='DIAGNOSTIC_NOT_INDEPENDENT',required_validation=('INDEPENDENT_PROVENANCE','TARGET_VALIDATION','NO_THRESHOLD_RELAXATION','SEPARATE_AUTHORIZATION'),blockers=BLOCKERS,provenance=p.provenance))
    result=(tuple(assessments),tuple(proposals))
    state=make(MetaLearningState,processed_ids=previous.processed_ids+(request_id,),consumed=previous.consumed+len(entries),remaining=previous.remaining-len(entries),sequence=sequence,previous_state_commitment=previous.commitment,policy_commitment=policy.commitment,history=previous.history+(digest((approved_input,result)),),provenance=previous.provenance)
    return state,*result,make(MetaLearningVerdict,status='ADVISORY_NOT_QUALIFIED',provenance=context.provenance)
