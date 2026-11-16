"""Pure audit of a supported LRN-007 invocation; missing gates stay unqualified."""
from qualification_contracts import *
def initial(): return make(QualificationState,processed_ids=(),consumed=0,remaining=32,sequence=0,previous_state_commitment='0'*64,history=(),provenance=())
def qualify(run_id,stages,findings,validation_inputs,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
    ident(run_id); check(previous,QualificationState); check(findings,FindingRegister)
    need(type(stages) is tuple and len(stages)==8,'STAGES')
    for stage in stages: check(stage,StageQualification)
    refs(tuple(x.stage_id for x in stages)); need(set(x.stage_id for x in stages)==set(STAGES),'MISSING_STAGE')
    for stage in stages:
        required=tuple(x[0] for x in FINDINGS if x[2]==stage.stage_id)
        need(set(required)<=set(stage.open_findings),'FINDING_SUPPRESSION')
    need(type(validation_inputs) is tuple and len(validation_inputs)==4,'VALIDATION_INPUTS')
    need(expected_state==previous.commitment and approved_input==digest((run_id,stages,findings,validation_inputs)),'HOST_PIN')
    integer(sequence); need(sequence==previous.sequence+1 and run_id not in previous.processed_ids,'REPLAY')
    v.m.t.r.s.replay.learning.memory.guard(stop,now,deadline,previous.remaining,8)
    candidate,chain,policy,state=validation_inputs
    result=v.validate(candidate,chain,policy,state,expected_state=state.commitment,approved_input=v.digest((candidate,chain,policy)),sequence=state.sequence+1,stop=stop,now=now,deadline=deadline)
    for flag in FLAGS: need(getattr(result[2],flag,None) is False,'SAFETY_BOUNDARY')
    assessment=result[1]; commitment=digest((validation_inputs,result))
    missing=tuple(sorted(set(assessment.provenance_assessment.missing+tuple(x.stage_id for x in stages if x.artifact_status=='UNAVAILABLE'))))
    inventory=make(EvidenceInventory,source_commitment=commitment,missing=missing,classification='STRUCTURALLY_BOUND_NOT_INDEPENDENT',provenance=('LOCAL_DIAGNOSTIC',))
    coverage=make(IntegrationCoverage,source_commitment=commitment,executed=('LRN-004','LRN-006','LRN-007'),unqualified=('LRN001_ORIGINAL_REPLAY','LRN002_ORIGINAL_REPLAY','LRN003_ORIGINAL_REPLAY','LRN005_ORIGINAL_REPLAY','INDEPENDENT_PROVENANCE','REAL_MEASUREMENTS'),synthetic=True,provenance=('LOCAL_DIAGNOSTIC',))
    safety=make(SafetyBoundaryAssessment,checked=FLAGS,not_established=('LRN001_LEARNING_FLAG','LRN001_STRATEGY_POLICY_FLAGS','LRN002_STRATEGY_POLICY_FLAGS','LRN003_STRATEGY_POLICY_FLAGS','LRN004_STRATEGY_POLICY_FLAGS','LRN005_STRATEGY_POLICY_FLAGS','FULL_PER_STAGE_RUNTIME_AUDIT'),source_commitment=digest(result[2]),provenance=('LRN007_ACTUAL_VERDICT',))
    readiness=make(LearningReadinessAssessment,dimensions=('ARCHITECTURE_IMPLEMENTED_PARTIAL','INTEGRATION_PARTIALLY_QUALIFIED','EVIDENCE_NOT_QUALIFIED','LEARNING_EXECUTION_NOT_AUTHORIZED','BLOCKED_BY_CRITICAL_FINDINGS'),priorities=PRIORITIES,provenance=('LOCAL_DIAGNOSTIC',))
    payload=(tuple(sorted(stages,key=lambda x:x.stage_id)),inventory,coverage,findings,safety,readiness)
    new=make(QualificationState,processed_ids=previous.processed_ids+(run_id,),consumed=previous.consumed+8,remaining=previous.remaining-8,sequence=sequence,previous_state_commitment=previous.commitment,history=previous.history+(digest((approved_input,payload)),),provenance=previous.provenance)
    return new,payload,make(QualificationVerdict,status='CLOSED PARTIAL',provenance=('LOCAL_DIAGNOSTIC',))
