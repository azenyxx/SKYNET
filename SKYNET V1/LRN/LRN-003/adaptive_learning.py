"""Pure bounded strategy diagnostics; no measured gains or learning permission."""
from learning_strategy_contracts import *


def initial(policy):
    policy.__post_init__()
    return make(StrategyState, processed_ids=(), consumed=0, remaining=policy.resource_ceiling,
                previous_state_commitment='0'*64, policy_commitment=policy.commitment, sequence=0, history=())


def evaluate(candidates, replay_args, replay_controls, policy, previous, *, expected_state,
             approved_input, sequence, stop=False, now=0, deadline=1):
    need(type(policy) is StrategyPolicy and type(previous) is StrategyState, 'CONTRACT')
    policy.__post_init__()
    previous.__post_init__()
    need(type(candidates) is tuple and 1 <= len(candidates) <= 8, 'CANDIDATE_LIMIT')
    need(type(replay_args) is tuple and len(replay_args) == 4, 'REPLAY_ARGS')
    need(type(replay_controls) is tuple and len(replay_controls) == 3, 'REPLAY_PINS')
    replay.learning.memory.guard(stop, now, deadline, previous.remaining, len(candidates))
    need(expected_state == previous.commitment, 'STALE_STATE')
    need(approved_input == digest((candidates, replay_args, replay_controls, policy.commitment)), 'INPUT_PIN')
    need(previous.policy_commitment == policy.commitment, 'POLICY_PIN')
    need(previous.consumed + previous.remaining == policy.resource_ceiling, 'BUDGET_ESCALATION')
    integer(sequence)
    need(sequence == previous.sequence + 1, 'SEQUENCE')
    for candidate in candidates:
        need(type(candidate) is StrategyCandidate, 'CANDIDATE')
        candidate.__post_init__()
    ids = tuple(c.strategy_id for c in candidates)
    refs(previous.processed_ids + ids)
    result = replay.replay(*replay_args, expected_state=replay_controls[0],
                           approved_request=replay_controls[1], expected_policy=replay_controls[2],
                           stop=stop, now=now, deadline=deadline)
    sources = replay_args[0]
    selected = set(result[1].selected_refs)
    selected_sources = tuple(s for s in sources if s.source_id in selected)
    evidence = make(StrategyEvidence, evidence_id='evidence:'+digest(result), replay_commitment=digest(result),
                    classifications=tuple(o.verification_status for o in result[3]),
                    outcomes=tuple(o.observed_source_status for o in result[3]),
                    source_commitments=tuple(sorted(s.source_commitment for s in selected_sources)),
                    source_diversity=len(set(s.record.source_evidence_commitment for s in selected_sources)))
    evaluations = []
    proposals = []
    for candidate in sorted(candidates, key=lambda c: (c.estimated_cost, c.strategy_id)):
        if candidate.category not in policy.categories:
            status, rationale = 'REJECTED', ('CATEGORY_DENIED',)
        elif candidate.estimated_cost > policy.max_estimated_cost:
            status, rationale = 'REJECTED', ('COST_EXCEEDED',)
        elif not selected_sources:
            status, rationale = 'BLOCKED', ('NO_SELECTED_EVIDENCE',)
        else:
            status, rationale = 'REQUIRES_MORE_EVIDENCE', ('DIAGNOSTIC_ONLY', 'INDEPENDENT_PROVENANCE_UNAVAILABLE')
        evaluations.append(make(StrategyEvaluation, strategy_id=candidate.strategy_id,
                                evidence_commitment=evidence.commitment, status=status,
                                rationale=rationale, estimated_cost=candidate.estimated_cost))
        proposals.append(make(AdaptationProposal, strategy_id=candidate.strategy_id,
            supporting_evidence=(evidence.evidence_id,), status=status, rationale=rationale,
            estimated_cost=candidate.estimated_cost,
            confidence_limitations='NO_MEASURED_GAIN_OR_INDEPENDENT_PROVENANCE',
            required_validation=('INDEPENDENT_EVIDENCE', 'SEPARATE_AUTHORIZATION'), blocking_findings=BLOCKERS))
    comparison = make(StrategyComparison, ordered_strategy_ids=tuple(e.strategy_id for e in evaluations),
                      basis='ESTIMATED_COST_THEN_ID_NO_GAIN_CLAIM')
    state = make(StrategyState, processed_ids=previous.processed_ids+tuple(sorted(ids)),
        consumed=previous.consumed+len(ids), remaining=previous.remaining-len(ids),
        previous_state_commitment=previous.commitment, policy_commitment=policy.commitment, sequence=sequence,
        history=previous.history+((approved_input, evidence.commitment, digest(tuple(proposals))),))
    return state, evidence, tuple(evaluations), comparison, tuple(proposals), make(StrategyVerdict,status='ADVISORY_ONLY')
