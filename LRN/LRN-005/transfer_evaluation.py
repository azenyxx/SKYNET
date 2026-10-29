"""Single-candidate, read-only transfer evaluation. No predecessor execution."""
from transfer_contracts import *
def initial(policy):
    check(policy,TransferPolicy)
    return make(TransferState,processed_ids=(),consumed=0,remaining=policy.budget,sequence=0,previous_state_commitment='0'*64,policy_commitment=policy.commitment,history=(),provenance=())
def evaluate(source,target,evidence,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
    for v,c in ((source,SourceDomainProfile),(target,TargetDomainProfile),(evidence,TransferEvidence),(policy,TransferPolicy),(previous,TransferState)): check(v,c)
    need(expected_state==previous.commitment and approved_input==digest((source,target,evidence,policy)),'HOST_PIN')
    need((source.domain_id,target.domain_id)==(policy.source_id,policy.target_id)==(evidence.source_id,evidence.target_id),'DOMAIN_BINDING')
    need(previous.policy_commitment==policy.commitment and previous.consumed+previous.remaining==policy.budget,'BUDGET')
    integer(sequence); need(sequence==previous.sequence+1,'SEQUENCE'); need(evidence.request_id not in previous.processed_ids,'DUPLICATE')
    r.s.replay.learning.memory.guard(stop,now,deadline,previous.remaining,1)
    need(bool(target.constraints) and set(source.constraints+target.constraints)<=set(policy.allowed_constraints),'CONSTRAINT_POLICY')
    covered=tuple(sorted(set(source.capabilities)&set(target.capabilities))); unsupported=tuple(sorted(set(target.capabilities)-set(source.capabilities)))
    reasons=[]
    if source.task_category!=target.task_category: reasons.append('TASK_MISMATCH')
    if (source.input_schema,source.output_schema)!=(target.input_schema,target.output_schema): reasons.append('SCHEMA_MISMATCH')
    if (source.metric_id,source.unit,source.direction)!=(target.metric_id,target.unit,target.direction): reasons.append('METRIC_INCOMPATIBLE')
    if source.constraints!=target.constraints: reasons.append('CONSTRAINT_MISMATCH')
    if unsupported: reasons.append('UNSUPPORTED_CAPABILITIES')
    compatibility='INCOMPATIBLE' if reasons else 'COMPATIBLE_FOR_EVALUATION'
    if not source.capabilities or not target.capabilities: compatibility='INSUFFICIENT_EVIDENCE'; reasons.append('EMPTY_CAPABILITIES')
    if not source.provenance or not target.provenance or not evidence.provenance: reasons.append('PROVENANCE_UNRESOLVED')
    original=evidence.adaptation.source
    if source.failures or any(x!='COMPLETED' for x in original.outcomes): reasons.append('SOURCE_FAILURE_OR_UNCERTAINTY')
    if any(x.status=='REGRESSION_DETECTED' for x in evidence.retention.assessments): reasons.append('SOURCE_RETENTION_REGRESSION')
    if evidence.retention.status!='RETENTION_PRESERVED': reasons.append('RETENTION_NOT_ESTABLISHED')
    need(len(set(original.source_commitments))==len(original.source_commitments),'DUPLICATE_EVIDENCE')
    for measurement in evidence.target_measurements:
        need((measurement.metric_id,measurement.unit,measurement.direction)==(target.metric_id,target.unit,target.direction),'TARGET_METRIC')
        if not measurement.provenance or measurement.quality!='DIAGNOSTIC': reasons.append('TARGET_PROVENANCE_UNRESOLVED')
    if not evidence.target_measurements: reasons.append('TARGET_MEASUREMENTS_MISSING')
    reasons.append('INDEPENDENT_PROVENANCE_NOT_ESTABLISHED')
    reasons=tuple(sorted(set(reasons)))
    assessment=make(CompatibilityAssessment,source_id=source.domain_id,target_id=target.domain_id,status=compatibility,examined=tuple(sorted(source.capabilities)),covered=covered,unsupported=unsupported,reasons=reasons,provenance=evidence.provenance)
    if compatibility=='INCOMPATIBLE': status='REJECTED'
    elif 'SOURCE_RETENTION_REGRESSION' in reasons or 'SOURCE_FAILURE_OR_UNCERTAINTY' in reasons: status='NEGATIVE_TRANSFER_RISK'
    elif not original.classifications or evidence.adaptation.proposal.status in ('REJECTED','BLOCKED','NOT_QUALIFIED'): status='NOT_QUALIFIED'
    else: status='REQUIRES_TARGET_EVIDENCE'
    counts=tuple((x,original.classifications.count(x)) for x in sorted(set(original.classifications)))
    candidate=make(TransferCandidate,request_id=evidence.request_id,source_id=source.domain_id,target_id=target.domain_id,status=status,assessment_commitment=assessment.commitment,evidence_commitment=evidence.commitment,reasons=reasons,trust_distribution=counts,excluded=evidence.adaptation.proposal.supporting_evidence if status in ('REJECTED','NOT_QUALIFIED') else (),provenance=evidence.provenance)
    state=make(TransferState,processed_ids=previous.processed_ids+(evidence.request_id,),consumed=previous.consumed+1,remaining=previous.remaining-1,sequence=sequence,previous_state_commitment=previous.commitment,policy_commitment=policy.commitment,history=previous.history+(candidate.commitment,),provenance=previous.provenance)
    return state,assessment,candidate,make(TransferVerdict,status='NOT_QUALIFIED',blockers=BLOCKERS,provenance=evidence.provenance)
