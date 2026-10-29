"""Structural recomputation is not independent scientific verification."""
import continual_retention as retention
from validation_contracts import *
def initial(policy):
    check(policy,ValidationPolicy)
    return make(ValidationState,processed_ids=(),consumed=0,remaining=policy.budget,sequence=0,previous_state_commitment='0'*64,policy_commitment=policy.commitment,history=(),provenance=())
def validate(candidate,chain,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
    for v,c in ((candidate,ValidationCandidate),(chain,EvidenceChain),(policy,ValidationPolicy),(previous,ValidationState)): check(v,c)
    need(expected_state==previous.commitment and approved_input==digest((candidate,chain,policy)),'HOST_PIN')
    need(previous.policy_commitment==policy.commitment and previous.consumed+previous.remaining==policy.budget,'BUDGET')
    integer(sequence); need(sequence==previous.sequence+1 and candidate.candidate_id not in previous.processed_ids,'REPLAY')
    cost=len(chain.entries)+1
    m.t.r.s.replay.learning.memory.guard(stop,now,deadline,previous.remaining,cost)
    need(candidate.chain_commitment==chain.commitment,'CHAIN_BINDING')
    reproduced=m.evaluate(chain.request_id,chain.context,chain.entries,chain.policy,chain.previous,expected_state=chain.previous.commitment,approved_input=m.digest((chain.request_id,chain.context,chain.entries,chain.policy)),sequence=chain.previous.sequence+1,stop=stop,now=now,deadline=deadline)
    need(reproduced==chain.result,'META_RESULT_MISMATCH')
    need(candidate.proposal in chain.result[2],'PROPOSAL_BINDING')
    pair=next((x for x in chain.entries if x[0].strategy_id==candidate.strategy_id),None); need(pair is not None,'MISSING_HISTORY'); h,p=pair
    e=h.evidence
    rs=retention.initial(e.retention_policy)
    rr=retention.evaluate(e.baseline,e.adaptation,e.retention_policy,rs,expected_state=rs.commitment,approved_input=retention.digest((e.baseline,e.adaptation,e.retention_policy)),sequence=1,stop=stop,now=now,deadline=deadline)
    need(rr[1]==e.retention,'RETENTION_RESULT_MISMATCH')
    original=e.adaptation.source
    need(len(set(original.source_commitments))==len(original.source_commitments),'DUPLICATE_SOURCE')
    failed=any(x!='COMPLETED' for x in original.outcomes)
    classification='CONTRADICTED' if 'CONTRADICTED' in original.classifications else ('UNAVAILABLE' if not original.classifications else 'STRUCTURALLY_BOUND')
    provenance=make(ProvenanceAssessment,source_commitment=chain.commitment,classification=classification,qualification='NOT_QUALIFIED',missing=('LRN001_ORIGINALS','LRN002_REPLAY_ARTIFACT','LRN005_POLICY','INDEPENDENT_VERIFIER'),original_classes=original.classifications,provenance=chain.provenance)
    mapping={'RETENTION_PRESERVED':'REGRESSION_GATE_PASSED','REGRESSION_DETECTED':'REGRESSION_DETECTED','INSUFFICIENT_EVIDENCE':'INSUFFICIENT_MEASUREMENTS','BASELINE_UNQUALIFIED':'BASELINE_UNQUALIFIED','NOT_QUALIFIED':'NOT_QUALIFIED'}
    gate=make(RegressionGate,baseline_commitment=e.baseline.commitment,retention_commitment=e.retention.commitment,status=mapping[e.retention.status],reasons=('RECOMPUTED_LOCAL_DIAGNOSTIC','MEASUREMENTS_NOT_INDEPENDENT'),provenance=e.retention.provenance)
    reasons=['INDEPENDENT_EVIDENCE_MISSING','ORIGINAL_ARTIFACTS_MISSING','INHERITED_BLOCKERS_OPEN']
    if not e.target_measurements: reasons.append('TARGET_MEASUREMENTS_MISSING')
    if h.verdict.status=='NOT_QUALIFIED': reasons.append('TRANSFER_NOT_QUALIFIED')
    if failed: reasons.append('SOURCE_OUTCOME_NOT_SUCCESS')
    if h.candidate.status=='NEGATIVE_TRANSFER_RISK': reasons.append('NEGATIVE_TRANSFER_RISK')
    if candidate.proposal.adjustment not in policy.allowed_adjustments or candidate.proposal.expected_cost>policy.max_cost: status='POLICY_BLOCKED'; reasons.append('POLICY_LIMIT')
    elif gate.status=='REGRESSION_DETECTED' or failed or h.candidate.status=='NEGATIVE_TRANSFER_RISK': status='REGRESSION_BLOCKED'
    elif h.assessment.status=='INCOMPATIBLE': status='REJECTED'
    else: status='INTEGRATION_NOT_QUALIFIED'
    assessment=make(ValidationAssessment,candidate_id=candidate.candidate_id,chain_commitment=chain.commitment,provenance_assessment=provenance,regression=gate,status=status,reasons=tuple(sorted(reasons)),blockers=BLOCKERS,provenance=candidate.provenance)
    state=make(ValidationState,processed_ids=previous.processed_ids+(candidate.candidate_id,),consumed=previous.consumed+cost,remaining=previous.remaining-cost,sequence=sequence,previous_state_commitment=previous.commitment,policy_commitment=policy.commitment,history=previous.history+(digest((approved_input,assessment)),),provenance=previous.provenance)
    return state,assessment,make(ValidationVerdict,status=status,provenance=candidate.provenance)
