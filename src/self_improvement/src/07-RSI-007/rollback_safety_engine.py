"""Pure declared snapshot simulation. No restoration, IO or candidate execution."""
from versioning_contracts import *
import improvement_selection_engine as upstream

def initial(policy):
 check(policy,SafetyValidationPolicy)
 return make(VersioningState,state_version='state-v1',sequence=0,previous_state_commitment='0'*64,registered_snapshots=(),evaluated_transitions=(),simulated_rollbacks=(),cumulative_resource_usage=0,policy_commitment=policy.commitment,history=())
def validate(source,target,transition,dependency,plan,restoration,governance_call,governance_result,policy,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
 for x,c in ((source,VersionSnapshot),(target,VersionSnapshot),(transition,VersionTransition),(dependency,VersionDependency),(plan,RollbackPlan),(policy,SafetyValidationPolicy),(previous,VersioningState)):check(x,c)
 need(type(restoration) is tuple and len(restoration)<=1,'RESTORATION')
 if restoration:check(restoration[0],VersionSnapshot)
 need(expected_state==previous.state_commitment and previous.policy_commitment==policy.commitment,'STATE_PIN');need(approved_input==digest((source,target,transition,dependency,plan,restoration,governance_call,governance_result,policy)),'INPUT_PIN');integer(sequence);need(sequence==previous.sequence+1 and transition.transition_id not in previous.evaluated_transitions and plan.rollback_id not in previous.simulated_rollbacks,'REPLAY')
 g.q.e.p.r.q.v.m.t.r.s.replay.learning.memory.guard(stop,now,deadline,policy.resource_limits-previous.cumulative_resource_usage,3)
 need(type(governance_call) is tuple and len(governance_call)==4 and type(governance_result) is tuple and len(governance_result)==5,'GOVERNANCE_SOURCE')
 entries,criteria,gpolicy,gstate=governance_call;g.check(gstate,g.GovernanceState)
 actual=upstream.select(*governance_call,expected_state=gstate.state_commitment,approved_input=g.digest((tuple(sorted(entries,key=lambda x:x[0].candidate_id)),tuple(sorted(criteria,key=lambda c:c.criterion_id)),gpolicy)),sequence=gstate.sequence+1,stop=stop,now=now,deadline=deadline)
 need(actual==governance_result and actual[4]=='NO_ELIGIBLE_CANDIDATE','GOVERNANCE_REPLAY')
 matches=[x for x in entries if x[0].candidate_id==transition.candidate_id];need(len(matches)==1,'CANDIDATE');candidate,ecall,eresult,auths=matches[0]
 gv=next(v for v in actual[3] if v.candidate_id==candidate.candidate_id)
 need(transition.governance_verdict_ref==gv.commitment and transition.evaluation_verdict_ref==eresult[3].commitment and transition.proposal_id==candidate.proposal_id,'VERDICT_BINDING')
 experiment=ecall[3][0]
 need(source.snapshot_id==transition.source_snapshot_id and target.snapshot_id==transition.target_snapshot_id and source.component_id==target.component_id==candidate.target_component,'SNAPSHOT_BINDING')
 need(source.component_version==candidate.target_version==experiment.target_version and target.component_version==experiment.candidate_version and source.component_version!=target.component_version,'VERSION_MISMATCH')
 need(source.source_commitment==experiment.baseline_ref and target.source_commitment==experiment.candidate_ref,'MEASURED_SUBJECT_BINDING')
 need(dependency.component_id==target.component_id and dependency.component_version==target.component_version,'DEPENDENCY_IDENTITY')
 need(plan.transition_id==transition.transition_id and plan.target_snapshot_id==source.snapshot_id,'PLAN_BINDING')
 dependency_ok=not dependency.unresolved_dependencies and set(dependency.required_dependencies)==set(target.dependency_commitments) and set(plan.dependency_requirements)==set(source.dependency_commitments)
 interface_ok=set(source.interface_commitments)==set(target.interface_commitments)==set(dependency.interface_constraints)
 restored=restoration[0] if restoration else None
 observed=restored.snapshot_commitment if restored else '0'*64
 sim_status='RESTORATION_EVIDENCE_REQUIRED' if restored is None else 'DEPENDENCY_BLOCKED' if not dependency_ok else 'STATE_INCOMPATIBLE' if not interface_ok else 'SIMULATION_PASSED' if restored==source else 'SIMULATION_FAILED'
 sim=make(RollbackSimulation,simulation_id=plan.rollback_id,rollback_id=plan.rollback_id,initial_state_commitment=target.snapshot_commitment,expected_state_commitment=source.snapshot_commitment,observed_simulated_commitment=observed,dependency_results=(('DECLARED_DEPENDENCIES','PASS' if dependency_ok else 'FAIL'),),invariant_results=(('EXACT_SNAPSHOT','PASS' if restored==source else 'FAIL'),('DECLARED_INTERFACES','PASS' if interface_ok else 'FAIL')),simulation_status=sim_status,limitations=('NO_ACTUAL_RESTORATION','NO_DURABILITY','HOST_SUPPLIED_SNAPSHOTS','NO_INDEPENDENT_PROVENANCE'))
 gates={'SOURCE_INTEGRITY':'PASS','TARGET_INTEGRITY':'PASS','VERSION_CONTINUITY':'PASS','DEPENDENCY_COMPATIBILITY':'NOT_QUALIFIED' if dependency_ok else 'FAIL','INTERFACE_COMPATIBILITY':'NOT_QUALIFIED' if interface_ok else 'FAIL','REGRESSION_STATUS':'FAIL' if eresult[3].regression_status=='OBSERVED' else 'NOT_QUALIFIED','GOVERNANCE_ELIGIBILITY':'FAIL','ROLLBACK_READINESS':'FAIL' if sim_status in ('SIMULATION_FAILED','DEPENDENCY_BLOCKED','STATE_INCOMPATIBLE') else 'NOT_QUALIFIED','AUTHORIZATION_BOUNDARY':'PASS','INHERITED_BLOCKERS':'FAIL'}
 verdict=make(SafetyValidationVerdict,transition_id=transition.transition_id,structural_validity=True,provenance_qualification='NOT_INDEPENDENTLY_QUALIFIED',compatibility_status='NOT_QUALIFIED',governance_status=actual[4],rollback_status=sim_status,safety_gate_results=tuple(sorted(gates.items())),unresolved_findings=BLOCKERS,decision='GOVERNANCE_BLOCKED',decision_reasons=('NO_ELIGIBLE_CANDIDATE','SIMULATION_IS_NOT_RESTORATION','INHERITED_P1_OPEN'),authorization_flags=tuple((f,False) for f in FLAGS))
 state=make(VersioningState,state_version='state-v1',sequence=sequence,previous_state_commitment=previous.state_commitment,registered_snapshots=tuple(sorted(set(previous.registered_snapshots+(source.snapshot_id,target.snapshot_id)))),evaluated_transitions=previous.evaluated_transitions+(transition.transition_id,),simulated_rollbacks=previous.simulated_rollbacks+(plan.rollback_id,),cumulative_resource_usage=previous.cumulative_resource_usage+3,policy_commitment=policy.commitment,history=previous.history+(digest((approved_input,sim,verdict)),))
 return state,sim,verdict
