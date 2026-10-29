"""Recorded diagnostic experience only. No task execution, learning or promotion.
Host pins bind scope and latest state but cannot prevent malicious host rollback.
Every source assessment is recomputed through the original LRN001 pure interface.
"""
from experience_replay_contracts import *


def initial(policy):
    policy.__post_init__()
    return make(ReplayState,processed_request_ids=(),replayed_batch_ids=(),consumed=0,
                remaining=policy.resource_ceiling,replay_operations=0,previous_state_commitment='0'*64,
                policy_commitment=policy.commitment,replayed_sources=(),history=())


def source_set(sources):
    need(type(sources) is tuple and len(sources)<=32, 'SOURCE_LIMIT')
    need(all(type(s) is ReplaySource for s in sources), 'SOURCE_TYPE')
    return digest(tuple(sorted(sources,key=lambda s:s.source_id)))


def replay(sources,request,policy,previous,*,expected_state,approved_request,
           expected_policy,stop=False,now=0,deadline=1):
    for obj,cls in ((request,SelectionRequest),(policy,SelectionPolicy),(previous,ReplayState)):
        need(type(obj) is cls, 'CONTRACT')
        obj.__post_init__()
    learning.memory.guard(stop,now,deadline,previous.remaining,1)
    need(previous.commitment==expected_state, 'STALE_STATE')
    need(request.commitment==approved_request, 'HOST_SCOPE')
    need(request.policy_commitment==policy.commitment==previous.policy_commitment==expected_policy, 'POLICY_PIN')
    need(request.source_set_commitment==source_set(sources), 'SOURCE_SET')
    need(request.sequence==len(previous.processed_request_ids)+1, 'SEQUENCE')
    need(request.request_id not in previous.processed_request_ids, 'REQUEST_REPLAY')
    need(previous.consumed+previous.remaining==policy.resource_ceiling, 'BUDGET_ESCALATION')
    refs(tuple(s.source_id for s in sources))
    refs(tuple(s.record.experience_id for s in sources))
    refs(tuple(s.evidence.evidence_id for s in sources))
    need(set(request.requested_scope)<=set(s.source_id for s in sources), 'SCOPE')
    need(len(sources)+1<=previous.remaining, 'BUDGET')
    validated=[]
    for source in sources:
        source.__post_init__()
        lp,ls,originals=source.verification_inputs
        output=learning.process(source.record,source.evidence,lp,ls,
            expected_state=ls.commitment,expected_policy=lp.commitment,
            approved_input=learning.digest((source.record,source.evidence)),
            originals=None if originals==() else originals)
        need(output[1]==source.assessment, 'ASSESSMENT_MISMATCH')
        validated.append((source,output[2]))
    priority={'PARTIALLY_VERIFIED':0,'REPORTED_ONLY':1,'NOT_ESTABLISHED':2,'UNAVAILABLE':3,'CONTRADICTED':4}
    def key(pair):
        s=pair[0]
        tie=(s.record.experience_id,s.source_id)
        if policy.ordering_strategy=='SOURCE_SEQUENCE':
            return (s.record.sequence,)+tie
        if policy.ordering_strategy=='VERIFICATION_PRIORITY':
            return (priority[s.assessment.evidence_validity],)+tie
        return tie
    validated.sort(key=key)
    groups={}
    for s,_ in validated:
        k=(s.record.source_evidence_commitment,s.record.task_id)
        groups.setdefault(k,set()).update((s.record.reported_outcome,s.evidence.observed_result))
    selected=[];excluded=[];reasons=[];seen=set(previous.replayed_sources)
    source_counts={};task_counts={};goal_counts={};trust_counts={};all_sources={}
    repeats=0;unresolved=0
    for s,signal in validated:
        trust=s.assessment.evidence_validity
        trust_counts[trust]=trust_counts.get(trust,0)+1
        origin=s.record.source_evidence_commitment
        all_sources[origin]=all_sources.get(origin,0)+1
        unresolved+=int(not s.evidence.provenance_ref)
        identity=digest((origin,s.record.task_id))
        reason=None
        if s.source_id not in request.requested_scope:
            reason='OUT_OF_SCOPE'
        elif trust=='CONTRADICTED':
            reason='CONTRADICTED'
        elif len(groups[(origin,s.record.task_id)])>1:
            reason='POTENTIAL_CONFLICT'
        elif not s.evidence.provenance_ref:
            reason='MISSING_PROVENANCE'
        elif trust not in policy.accepted_trust_classes:
            reason='TRUST_POLICY'
        elif identity in seen:
            reason='DUPLICATE_EVIDENCE';repeats+=1
        elif (len(selected)>=policy.max_batch or source_counts.get(origin,0)>=policy.per_source
              or task_counts.get(s.record.task_id,0)>=policy.per_task
              or goal_counts.get(s.record.goal_id,0)>=policy.per_goal):
            reason='QUOTA'
        if reason:
            excluded.append(s.source_id);reasons.append(reason)
        else:
            selected.append((s,signal,identity));seen.add(identity)
            source_counts[origin]=source_counts.get(origin,0)+1
            task_counts[s.record.task_id]=task_counts.get(s.record.task_id,0)+1
            goal_counts[s.record.goal_id]=goal_counts.get(s.record.goal_id,0)+1
    need(previous.replay_operations+len(selected)<=policy.max_operations, 'OPERATION_LIMIT')
    selection=make(EvidenceSelection,selection_id='selection:'+request.request_id,
        selected_refs=tuple(s.source_id for s,_,_ in selected),excluded_refs=tuple(excluded),
        exclusion_reasons=tuple(reasons),source_commitments=tuple(s.commitment for s,_ in validated),
        coverage=(len(sources),len(selected),len(excluded),repeats,unresolved,
                  tuple(sorted(trust_counts.items())),tuple(sorted(all_sources.items()))))
    batch=make(ReplayBatch,batch_id='batch:'+request.request_id,
        ordered_experience_refs=tuple(s.record.experience_id for s,_,_ in selected),
        sequence_start=previous.replay_operations,sequence_end=previous.replay_operations+len(selected),
        source_set_commitment=request.source_set_commitment,selection_commitment=selection.commitment)
    need(batch.batch_id not in previous.replayed_batch_ids, 'BATCH_REPLAY')
    observations=tuple(make(ReplayObservation,observation_id='observation:'+s.record.experience_id,
        batch_id=batch.batch_id,replay_position=previous.replay_operations+i,
        observed_source_status=signal.outcome_attribution if signal.outcome_attribution!='UNKNOWN' else s.record.reported_outcome,
        verification_status=s.assessment.evidence_validity,source_eligibility=s.assessment.eligibility_status)
        for i,(s,signal,_) in enumerate(selected,1))
    cost=len(sources)+1
    state=make(ReplayState,processed_request_ids=previous.processed_request_ids+(request.request_id,),
        replayed_batch_ids=previous.replayed_batch_ids+(batch.batch_id,),consumed=previous.consumed+cost,
        remaining=previous.remaining-cost,replay_operations=previous.replay_operations+len(selected),
        previous_state_commitment=previous.commitment,policy_commitment=policy.commitment,
        replayed_sources=previous.replayed_sources+tuple(identity for _,_,identity in selected),
        history=previous.history+((request.commitment,selection.commitment,batch.commitment,digest(observations)),))
    verdict=make(ReplayVerdict,selection_status='SELECTED_FOR_DIAGNOSTIC_REPLAY' if selected else 'EXCLUDED',
        replay_status='DIAGNOSTIC_REPLAY_ONLY' if selected else 'EMPTY',
        evidence_qualification='REQUIRES_VERIFICATION',blocking_findings=BLOCKERS)
    return state,selection,batch,observations,verdict
