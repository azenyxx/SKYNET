"""Offline assessment only. Never dispatches tasks or establishes source authenticity.
Host must pin current state, policy, evidence and registry snapshots. No durability.
"""
from agent_qualification_contracts import *

# Owner-supplied open debt; historical closure is never inferred from test scores.
DEBT = (
    ('A01-001','P1','AGT001','Budget transition helper'),
    ('A01-002','P1','AGT001','Trace semantics'),
    ('A01-003','P2','AGT001','Interruption and recovery'),
    ('A02-001','P1','AGT002','Exception accounting'),
    ('A02-002','P1','AGT002','Output semantics'),
    ('A04-002','P2','AGT004','Independent provenance'),
    ('A06-001','P1','AGT006','Post-execution replanning'),
    ('A06-002','P2','AGT006','Constraints and candidate evaluation'),
    ('A07-001','P1','AGT007','Collaboration integration'),
    ('A07-002','P2','AGT007','Existing test error'),
    ('A07-003','P1','AGT007','Decision coverage'),
    ('A07-004','P2','AGT007','Snapshot bounds'),
    ('A08-001','P1','AGT008','Continuation reassignment replan'),
    ('A08-002','P2','AGT008','Recovery matrix'),
    ('A09-001','P1','AGT009','Tuple lookup raises TypeError; five historical errors'),
    ('A09-002','P1','AGT009','Lifecycle dependency qualification'),
    ('A09-003','P2','AGT009','Incomplete tests'),
    ('A09-004','P1','AGT009','Host authentication rollback'),
    ('C20-001','P1','COG020','Forged evidence references'),
    ('C20-002','P2','COG020','Extreme rational qualification'),
)


def inherited_findings():
    return tuple(make(FindingRecord, finding_id=i, severity=s, affected_components=(c,),
                      description=d, status='OPEN', supporting_evidence=('OWNER_SPEC_AND_PRIOR_REPORTS',))
                 for i, s, c, d in DEBT)


def initial(policy):
    policy.__post_init__()
    return make(QualificationState, processed_evidence_ids=(), assessed_capabilities=(),
                unresolved_findings=tuple(sorted(x[0] for x in DEBT)),
                previous_state_commitment='0'*64, consumed=0,
                remaining=policy.resource_ceiling, history=())


def graph(components, edges):
    require(type(components) is tuple and 0 < len(components) <= 32, 'COMPONENT_LIMIT')
    require(type(edges) is tuple and len(edges) <= 64, 'EDGE_LIMIT')
    nodes = {}
    for obj in components:
        require(type(obj) is ComponentDescriptor, 'COMPONENT')
        obj.__post_init__()
        require(obj.component_id not in nodes, 'DUPLICATE_COMPONENT')
        nodes[obj.component_id] = obj
    dependencies = {k: set(v.dependencies) for k, v in nodes.items()}
    for node, deps in dependencies.items():
        require(deps <= nodes.keys(), 'UNKNOWN_DEPENDENCY')
    seen = set()
    for edge in edges:
        require(type(edge) is IntegrationDependency, 'EDGE')
        edge.__post_init__()
        require(edge.source_id in nodes and edge.target_id in nodes, 'UNKNOWN_DEPENDENCY')
        require(edge.required_interface in nodes[edge.target_id].interfaces, 'UNSUPPORTED_INTERFACE')
        key = (edge.source_id, edge.target_id, edge.required_interface)
        require(key not in seen, 'DUPLICATE_EDGE')
        seen.add(key)
        dependencies[edge.source_id].add(edge.target_id)
    order = []
    while len(order) < len(nodes):
        ready = sorted(k for k in nodes if k not in order and dependencies[k] <= set(order))
        require(bool(ready), 'CYCLE')
        order.extend(ready)
    return tuple(order), dependencies


def assess(components, edges, evidence, findings, policy, previous, *,
           expected_state, expected_snapshot, expected_policy, approved_evidence,
           sequence, stop=False, now=0, deadline=1):
    require(type(stop) is bool and not stop, 'STOP')
    require(type(now) is int and type(deadline) is int and 0 <= now < deadline, 'DEADLINE')
    require(type(previous) is QualificationState and type(policy) is QualificationPolicy, 'CONTRACT')
    previous.__post_init__()
    policy.__post_init__()
    require(expected_state == previous.commitment, 'STALE_STATE')
    require(expected_policy == policy.commitment, 'POLICY_PIN')
    require(expected_snapshot == digest((components, edges, findings)), 'SNAPSHOT_PIN')
    require(type(sequence) is int and sequence == previous.consumed + 1, 'SEQUENCE')
    require(type(evidence) is tuple and 0 < len(evidence) <= 32, 'EVIDENCE_LIMIT')
    require(type(findings) is tuple and len(findings) <= 128, 'FINDING_LIMIT')
    require(type(approved_evidence) is tuple and len(approved_evidence) <= 256, 'HOST_PIN')
    order, dependencies = graph(components, edges)
    debt = {f.finding_id: f for f in findings}
    require(len(debt) == len(findings), 'DUPLICATE_FINDING')
    for obj in findings:
        require(type(obj) is FindingRecord, 'FINDING')
        obj.__post_init__()
    for mandatory in inherited_findings():
        require(debt.get(mandatory.finding_id) == mandatory, 'DEBT_SUPPRESSION')
    require(set(previous.unresolved_findings) <= debt.keys(), 'DEBT_LOSS')
    require(previous.consumed + previous.remaining == policy.resource_ceiling, 'BUDGET_ESCALATION')
    require(len(evidence) <= previous.remaining, 'BUDGET')
    ids = []
    for item in evidence:
        require(type(item) is QualificationEvidence, 'EVIDENCE')
        item.__post_init__()
        require(item.component_id in order, 'UNKNOWN_COMPONENT')
        require(item.commitment in approved_evidence, 'UNPINNED_EVIDENCE')
        require(item.evidence_id not in previous.processed_evidence_ids + tuple(ids), 'REPLAY')
        require(not (item.component_id == 'AGT009' and item.observed_result == 'PASS'), 'FALSE_PASS_AGT009')
        ids.append(item.evidence_id)
    # Even host-pinned PASS does not establish independent verification or full capability.
    statuses = {}
    assessments = []
    for component in order:
        own = tuple(x for x in evidence if x.component_id == component)
        blocking = tuple(sorted(f.finding_id for f in findings
                                if f.severity == 'P1' and component in f.affected_components))
        if blocking or any(statuses[x] in ('BLOCKED', 'FAILED', 'EVIDENCE_UNAVAILABLE') for x in dependencies[component]):
            status = 'BLOCKED'
        elif any(x.observed_result in ('FAIL', 'ERROR') for x in own):
            status = 'FAILED'
        elif len(own) < policy.minimum_evidence:
            status = 'EVIDENCE_UNAVAILABLE'
        else:
            status = 'QUALIFIED_PARTIAL'
        statuses[component] = status
        assessments.append(make(CapabilityAssessment, capability_id=component,
                                supporting_components=(component,), required_evidence=tuple(x.evidence_id for x in own),
                                qualification_status=status, blocking_findings=blocking))
    overall = 'BLOCKED' if any(v in ('BLOCKED', 'FAILED') for v in statuses.values()) else 'QUALIFIED_PARTIAL'
    require(overall in policy.permitted_verdicts, 'POLICY_VERDICT')
    new = make(QualificationState, processed_evidence_ids=previous.processed_evidence_ids + tuple(ids),
               assessed_capabilities=tuple(sorted(statuses)), unresolved_findings=tuple(sorted(debt)),
               previous_state_commitment=previous.commitment, consumed=previous.consumed + len(ids),
               remaining=previous.remaining - len(ids),
               history=previous.history + ((digest(evidence), expected_snapshot, policy.commitment),))
    verdict = make(QualificationVerdict, component_statuses=tuple(sorted(statuses.items())),
                   integration_status=overall, verification_status='NOT_ESTABLISHED',
                   blocking_findings=tuple(sorted(f.finding_id for f in findings if f.severity == 'P1')))
    return new, tuple(assessments), verdict
