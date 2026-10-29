"""Pure diagnostic ingestion. AGT004 local consistency is not independent provenance.
No VERIFIED_LOCAL producer is available here: matching originals remain PARTIALLY_VERIFIED.
Rejected eligibility is recorded and costs one processing unit; malformed requests
raise before committing a new state. Caller must retain trusted latest host pins.
"""
from learning_contracts import *
import agent_memory as memory


def source_commitment(arguments, result):
    need(type(arguments) is tuple and type(result) is tuple, 'SOURCE_TYPE')
    encoded = memory.encoded((arguments, result))
    need(len(encoded) <= 262144, 'SOURCE_LIMIT')
    return memory.digest('LRN001-original', (arguments, result))


def initial(policy):
    need(type(policy) is LearningPolicy, 'POLICY')
    policy.__post_init__()
    return make(LearningState, processed_experience_ids=(), accepted_evidence_refs=(),
                rejected_evidence_refs=(), candidate_refs=(), consumed=0,
                remaining=policy.max_processing_budget, previous_state_commitment='0'*64,
                policy_commitment=policy.commitment, source_refs=(), history=())


def process(record, evidence, policy, previous, *, expected_state, expected_policy,
            approved_input, originals=None, stop=False, now=0, deadline=1):
    for obj, cls in ((record, ExperienceRecord), (evidence, OutcomeEvidence),
                     (policy, LearningPolicy), (previous, LearningState)):
        need(type(obj) is cls, 'CONTRACT')
        obj.__post_init__()
    memory.guard(stop, now, deadline, previous.remaining, 1)
    need(expected_state == previous.commitment, 'STALE_STATE')
    need(expected_policy == policy.commitment == previous.policy_commitment, 'POLICY_PIN')
    need(previous.consumed + previous.remaining == policy.max_processing_budget, 'BUDGET_ESCALATION')
    need(approved_input == digest((record, evidence)), 'INPUT_PIN')
    need(record.experience_id == evidence.experience_id, 'EXPERIENCE_BINDING')
    need(record.experience_id not in previous.processed_experience_ids, 'REPLAY')
    need(evidence.evidence_id not in previous.accepted_evidence_refs + previous.rejected_evidence_refs, 'EVIDENCE_REPLAY')
    need(record.sequence == previous.consumed + 1, 'SEQUENCE')
    source_ref = digest((record.source_evidence_commitment, record.task_id))
    need(source_ref not in previous.source_refs, 'SOURCE_REPLAY')
    need(evidence.verification_level in policy.allowed_evidence_classes, 'EVIDENCE_POLICY')
    need(evidence.verification_level != 'VERIFIED_LOCAL', 'UNSUPPORTED_VERIFICATION_CLAIM')
    validity = 'REPORTED_ONLY'
    eligibility = 'REQUIRES_VERIFICATION'
    reasons = ('NO_INDEPENDENT_PROVENANCE',)
    attribution = 'UNKNOWN'
    if originals is not None:
        need(type(originals) is tuple and len(originals) == 2, 'ORIGINALS')
        arguments, result = originals
        need(source_commitment(arguments, result) == record.source_evidence_commitment, 'SOURCE_BINDING')
        need(arguments[0] == record.workflow_id, 'WORKFLOW_BINDING')
        verified = memory.ingest_governance(arguments, result)
        match = next((item for item in verified if item.task_id == record.task_id), None)
        need(match is not None and match.agent_id == record.agent_id, 'TASK_AGENT_BINDING')
        need(evidence.provenance_ref == match.experience_id, 'PROVENANCE_BINDING')
        attribution = match.execution_status
        validity = 'PARTIALLY_VERIFIED'
        if record.reported_outcome != attribution or evidence.observed_result != attribution:
            validity = 'CONTRADICTED'
    elif evidence.verification_level == 'PARTIALLY_VERIFIED':
        raise ValueError('MISSING_VERIFICATION_ARTIFACTS')
    if not evidence.provenance_ref:
        validity, eligibility, reasons = 'UNAVAILABLE', 'BLOCKED', ('MISSING_PROVENANCE',)
    elif evidence.verification_level == 'CONTRADICTED' or validity == 'CONTRADICTED':
        validity, eligibility, reasons = 'CONTRADICTED', 'REJECTED', ('CONTRADICTED_OUTCOME',)
    elif evidence.verification_level in ('UNAVAILABLE', 'NOT_ESTABLISHED'):
        validity, eligibility, reasons = evidence.verification_level, 'NOT_QUALIFIED', ('INSUFFICIENT_EVIDENCE',)
    assessment = make(ExperienceAssessment, experience_id=record.experience_id,
                      evidence_validity=validity, eligibility_status=eligibility,
                      confidence_category='CALLER_REPORTED_UNCALIBRATED', rejection_reasons=reasons)
    signal = make(LearningSignal, signal_id='signal:'+digest((record.commitment, evidence.commitment)),
                  experience_id=record.experience_id, feedback_category='DIAGNOSTIC_ONLY',
                  outcome_attribution=attribution, signal_quality=validity)
    # No accepted qualified evidence or candidates are emitted while provenance remains unqualified.
    state = make(LearningState, processed_experience_ids=previous.processed_experience_ids+(record.experience_id,),
                 accepted_evidence_refs=previous.accepted_evidence_refs,
                 rejected_evidence_refs=previous.rejected_evidence_refs+(evidence.evidence_id,),
                 candidate_refs=previous.candidate_refs, consumed=previous.consumed+1, remaining=previous.remaining-1,
                 previous_state_commitment=previous.commitment, policy_commitment=policy.commitment,
                 source_refs=previous.source_refs+(source_ref,),
                 history=previous.history+((record.commitment, evidence.commitment, assessment.commitment,
                                           signal.commitment, approved_input),))
    verdict = make(LearningVerdict, processing_status='RECORDED_DIAGNOSTIC', evidence_qualification=validity,
                   learning_eligibility=eligibility, reason_codes=reasons)
    return state, assessment, signal, verdict
