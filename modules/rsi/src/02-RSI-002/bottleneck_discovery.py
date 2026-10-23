"""Pure bounded diagnostics. No remediation or independently verified claims."""
from self_assessment_contracts import *
import self_improvement_foundation as predecessor

def initial(policy):
    check(policy,AssessmentPolicy)
    return make(AssessmentState,state_version='state-v1',sequence=0,previous_state_commitment='0'*64,assessed_components=(),registered_bottlenecks=(),cumulative_resource_usage=0,policy_commitment=policy.commitment,history=())
def priority(items):
    need(type(items) is tuple and len(items)<=32,'BOUND')
    for o,d,risk in items:
        check(o,BottleneckObservation); check(d,DependencyImpact); need(d.bottleneck_id==o.bottleneck_id,'BINDING'); need(risk in ('LOW','MEDIUM','HIGH'),'RISK')
    strings(tuple(o.bottleneck_id for o,d,risk in items))
    return tuple(o.bottleneck_id for o,d,risk in sorted(items,key=lambda x:(0 if x[0].bottleneck_type=='SECURITY_BOUNDARY' else 1,0 if x[0].observed_impact=='LOCAL_DIAGNOSTIC' else 1,-len(x[1].downstream_dependencies),0 if x[0].confidence_class=='SUSPECTED' else 1,('HIGH','MEDIUM','LOW').index(x[2]),x[0].bottleneck_id)))
def assess(snapshot,metrics,category,dependency,inputs,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
    check(snapshot,ComponentSnapshot); check(policy,AssessmentPolicy); check(previous,AssessmentState); check(dependency,DependencyImpact)
    need(type(metrics) is tuple and len(metrics)<=8,'METRICS')
    for m in metrics: check(m,AssessmentMetric); need(m.component_id==snapshot.component_id,'COMPONENT')
    strings(tuple(m.metric_id for m in metrics)); strings(tuple(m.measurement_source for m in metrics))
    need(category in policy.permitted_assessment_types,'CATEGORY')
    need(type(inputs) is tuple and len(inputs)==7,'RSI_INPUTS')
    o,h,p,ev,risk,rpolicy,rstate=inputs
    for x,c in ((o,r.ImprovementObservation),(h,r.ImprovementHypothesis),(p,r.ChangeProposal),(risk,r.ImprovementRiskAssessment),(rpolicy,r.ImprovementPolicy),(rstate,r.ImprovementState)): r.check(x,c)
    need(type(ev) is tuple and len(ev)<=8,'EVIDENCE')
    for e in ev: r.check(e,r.ImprovementEvidence)
    need(snapshot.component_id==o.component_id and snapshot.component_version==o.component_version,'COMPONENT')
    need(set(snapshot.evidence_refs)==set(o.evidence_refs),'EVIDENCE_BINDING')
    need(expected_state==previous.state_commitment and previous.policy_commitment==policy.commitment,'STATE_PIN')
    ordered=tuple(sorted(metrics,key=lambda x:x.metric_id))
    need(approved_input==digest((snapshot,ordered,category,dependency,inputs,policy)),'INPUT_PIN')
    integer(sequence); need(sequence==previous.sequence+1 and snapshot.component_id not in previous.assessed_components,'REPLAY')
    cost=1+len(metrics)+len(ev)
    r.q.v.m.t.r.s.replay.learning.memory.guard(stop,now,deadline,policy.resource_limits-previous.cumulative_resource_usage,cost)
    need(dependency.bottleneck_id==o.observation_id and snapshot.component_id not in dependency.upstream_dependencies+dependency.downstream_dependencies,'DEPENDENCY_CYCLE')
    need(set(dependency.affected_interfaces)<=set(snapshot.interface_commitments),'INTERFACE')
    result=predecessor.assess(*inputs,expected_state=rstate.state_commitment,approved_input=r.digest((o,h,p,ev,risk,rpolicy,None)),sequence=rstate.sequence+1)
    r.check(result[2],r.ImprovementVerdict)
    need(all(v is False for k,v in result[2].authorization_flags),'AUTHORITY')
    need(p.change_type in rpolicy.permitted_proposal_types,'UNAUTHORIZED_PROPOSAL')
    evidence=tuple(make(BottleneckEvidence,evidence_id=e.evidence_id,observation_id=o.observation_id,source_stage='RSI-001',evidence_type='LOCAL_DIAGNOSTIC',provenance_class=e.provenance_class,verification_status='NOT_INDEPENDENTLY_QUALIFIED',source_commitment=e.commitment,limitations=e.limitations) for e in sorted(ev,key=lambda x:x.evidence_id))
    conflict=o.provenance_class=='CONTRADICTED' or any(e.provenance_class=='CONTRADICTED' for e in ev)
    grouped={}
    for m in ordered: grouped.setdefault((m.metric_name,m.unit,m.measurement_context),set()).add(m.value)
    conflict=conflict or any(len(v)>1 for v in grouped.values())
    status='CONTRADICTED' if conflict else 'SUSPECTED' if evidence and metrics else 'UNSUPPORTED'
    observation=make(BottleneckObservation,bottleneck_id=o.observation_id,component_id=o.component_id,bottleneck_type=category,affected_capabilities=snapshot.capability_ids,supporting_evidence=tuple(e.evidence_id for e in evidence),observed_impact='LOCAL_DIAGNOSTIC' if metrics else 'UNKNOWN',confidence_class=status,source_commitment=digest((result,ordered,evidence)))
    order=priority(((observation,dependency,h.risk_class),))
    verdict=make(AssessmentVerdict,component_id=o.component_id,identified_bottlenecks=order,evidence_qualification='NOT_INDEPENDENTLY_QUALIFIED',dependency_assessment='DECLARED_NOT_VERIFIED',priority_order=order,unresolved_findings=BLOCKERS,assessment_status=status,decision_reasons=('INHERITED_P1_OPEN','NO_INDEPENDENT_VERIFIER','NO_BASELINE_QUALIFICATION','ADVISORY_ONLY'),authorization_flags=tuple((x,False) for x in FLAGS))
    state=make(AssessmentState,state_version='state-v1',sequence=sequence,previous_state_commitment=previous.state_commitment,assessed_components=previous.assessed_components+(o.component_id,),registered_bottlenecks=previous.registered_bottlenecks+(o.observation_id,),cumulative_resource_usage=previous.cumulative_resource_usage+cost,policy_commitment=policy.commitment,history=previous.history+(digest((approved_input,observation,verdict)),))
    return state,observation,evidence,verdict
