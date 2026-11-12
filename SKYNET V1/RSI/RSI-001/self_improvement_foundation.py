"""Pure proposal management. No IO, evaluation of code or approval issuer."""
from rsi_contracts import *
def initial(policy):
    check(policy,ImprovementPolicy)
    return make(ImprovementState,state_version='rsi-state-v1',sequence=0,previous_state_commitment='0'*64,registered_proposal_ids=(),evaluated_proposal_ids=(),rejected_proposal_ids=(),cumulative_resource_usage=0,policy_commitment=policy.commitment,history=())
def consume_lrn(result):
    need(type(result) is tuple and len(result)==3,'LRN_RESULT')
    check(result[0],q.QualificationState); check(result[2],q.QualificationVerdict)
    payload=result[1]; need(type(payload) is tuple and len(payload)==6,'LRN_PAYLOAD')
    need(type(payload[0]) is tuple and len(payload[0])==8,'STAGES')
    for stage in payload[0]: check(stage,q.StageQualification)
    need(tuple(x.stage_id for x in payload[0])==q.STAGES,'STAGES')
    for x,c in zip(payload[1:],(q.EvidenceInventory,q.IntegrationCoverage,q.FindingRegister,q.SafetyBoundaryAssessment,q.LearningReadinessAssessment)): check(x,c)
    for flag in q.FLAGS: need(getattr(result[2],flag) is False,'LRN_AUTHORITY')
    return make(ImprovementEvidence,evidence_id='lrn008-diagnostic',source_stage='LRN-008',source_artifact='qualification-result-v1',evidence_type='LOCAL_DIAGNOSTIC',provenance_class='STRUCTURALLY_BOUND',source_commitment=digest(result),verification_status='NOT_QUALIFIED',limitations=('INDEPENDENT_PROVENANCE_UNAVAILABLE','LRN_CLOSED_PARTIAL','ORIGINALS_INCOMPLETE'))
def assess(observation,hypothesis,proposal,evidence,risk,policy,previous,*,expected_state,approved_input,sequence,lrn_result=None,stop=False,now=0,deadline=1):
    for x,c in ((observation,ImprovementObservation),(hypothesis,ImprovementHypothesis),(proposal,ChangeProposal),(risk,ImprovementRiskAssessment),(policy,ImprovementPolicy),(previous,ImprovementState)): check(x,c)
    need(type(evidence) is tuple and len(evidence)<=8,'EVIDENCE_BOUND')
    for x in evidence: check(x,ImprovementEvidence)
    refs(tuple(x.evidence_id for x in evidence)); refs(tuple(x.source_commitment for x in evidence))
    need(expected_state==previous.state_commitment and previous.policy_commitment==policy.commitment,'STATE_PIN')
    need(approved_input==digest((observation,hypothesis,proposal,evidence,risk,policy,lrn_result)),'INPUT_PIN')
    integer(sequence); need(sequence==previous.sequence+1 and proposal.proposal_id not in previous.registered_proposal_ids,'REPLAY')
    q.v.m.t.r.s.replay.learning.memory.guard(stop,now,deadline,policy.resource_limits-previous.cumulative_resource_usage,2)
    need(hypothesis.observation_id==observation.observation_id and proposal.hypothesis_id==hypothesis.hypothesis_id,'HYPOTHESIS_BINDING')
    need(observation.component_id==hypothesis.target_component==proposal.target_component and observation.component_version==proposal.target_version,'TARGET_BINDING')
    need(risk.proposal_id==proposal.proposal_id,'RISK_BINDING')
    need(set(observation.evidence_refs)==set(x.evidence_id for x in evidence),'EVIDENCE_REFS')
    if evidence: need(observation.source_commitment==digest(evidence),'SOURCE_BINDING')
    if lrn_result is not None: need(consume_lrn(lrn_result) in evidence,'LRN_BINDING')
    compliant=proposal.change_type in policy.permitted_proposal_types
    reasons=['INHERITED_P1_OPEN','NO_EXECUTION_AUTHORITY','INDEPENDENT_PROVENANCE_UNAVAILABLE']
    if not compliant: decision='POLICY_BLOCKED'; reasons.append('UNAUTHORIZED_CHANGE_TYPE')
    elif hypothesis.risk_class=='HIGH' or (hypothesis.risk_class=='MEDIUM' and policy.risk_thresholds=='LOW') or risk.security_risks: decision='RISK_BLOCKED'; reasons.append('RISK_THRESHOLD')
    elif observation.provenance_class=='CONTRADICTED' or any(x.provenance_class=='CONTRADICTED' for x in evidence): decision='REJECTED'; reasons.append('CONTRADICTED_EVIDENCE')
    elif not evidence: decision='REQUIRES_EVIDENCE'; reasons.append('MISSING_EVIDENCE')
    else: decision='INTEGRATION_NOT_QUALIFIED'; reasons.append('LRN_CLOSED_PARTIAL' if lrn_result is not None else 'ORIGINAL_RESULT_UNAVAILABLE')
    verdict=make(ImprovementVerdict,proposal_id=proposal.proposal_id,structural_validity=True,evidence_qualification='NOT_QUALIFIED',policy_compliance=compliant,risk_classification=hypothesis.risk_class,unresolved_findings=BLOCKERS,decision=decision,decision_reasons=tuple(sorted(reasons)),authorization_flags=tuple((x,False) for x in FLAGS))
    ids=previous.registered_proposal_ids+(proposal.proposal_id,)
    state=make(ImprovementState,state_version='rsi-state-v1',sequence=sequence,previous_state_commitment=previous.state_commitment,registered_proposal_ids=ids,evaluated_proposal_ids=ids,rejected_proposal_ids=previous.rejected_proposal_ids+((proposal.proposal_id,) if decision=='REJECTED' else ()),cumulative_resource_usage=previous.cumulative_resource_usage+2,policy_commitment=policy.commitment,history=previous.history+(digest((approved_input,LIFECYCLE,verdict)),))
    return state,LIFECYCLE,verdict
