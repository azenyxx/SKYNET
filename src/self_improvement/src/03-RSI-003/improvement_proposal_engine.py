"""Deterministic advisory construction using actual RSI-002 replay."""
from improvement_hypothesis_contracts import *
import bottleneck_discovery as upstream
MAPPING=dict(zip(s.TYPES,('ALGORITHM_REFINEMENT','RELIABILITY_IMPROVEMENT','VALIDATION_STRENGTHENING','RESOURCE_OPTIMIZATION','INTEGRATION_REPAIR','EVIDENCE_RECOVERY','VALIDATION_STRENGTHENING','EVIDENCE_RECOVERY','UNKNOWN')))
def initial(budget=16):return make(ProposalState,state_version='state-v1',sequence=0,previous_state_commitment='0'*64,registered_hypotheses=(),registered_proposals=(),rejected_proposals=(),cumulative_resource_usage=0,budget=budget,history=())
def construct(source_args,source_result,hypothesis_id,proposal_id,metric,direction,baseline,previous,*,expected_state,approved_input,sequence,stop=False,now=0,deadline=1):
 check(previous,ProposalState)
 for x in (hypothesis_id,proposal_id,metric):ident(x)
 need(type(source_args) is tuple and len(source_args)==7,'SOURCE_ARGS');need(type(source_result) is tuple and len(source_result)==4,'SOURCE_RESULT')
 snapshot,metrics,category,dependency,inputs,policy,state=source_args
 s.check(snapshot,s.ComponentSnapshot);s.check(policy,s.AssessmentPolicy);s.check(state,s.AssessmentState);s.check(dependency,s.DependencyImpact)
 for x,c in zip((source_result[0],source_result[1],source_result[3]),(s.AssessmentState,s.BottleneckObservation,s.AssessmentVerdict)):s.check(x,c)
 need(type(source_result[2]) is tuple and len(source_result[2])<=8,'EVIDENCE')
 for e in source_result[2]:s.check(e,s.BottleneckEvidence)
 need(expected_state==previous.state_commitment,'STATE_PIN');need(approved_input==digest((source_args,source_result,hypothesis_id,proposal_id,metric,direction,baseline)),'INPUT_PIN')
 integer(sequence);need(sequence==previous.sequence+1,'SEQUENCE');need(hypothesis_id not in previous.registered_hypotheses and proposal_id not in previous.registered_proposals,'DUPLICATE')
 r.q.v.m.t.r.s.replay.learning.memory.guard(stop,now,deadline,previous.budget-previous.cumulative_resource_usage,2)
 need(type(metrics) is tuple and len(metrics)<=8,'METRICS');ordered=tuple(sorted(metrics,key=lambda x:x.metric_id))
 reproduced=upstream.assess(*source_args,expected_state=state.state_commitment,approved_input=s.digest((snapshot,ordered,category,dependency,inputs,policy)),sequence=state.sequence+1,stop=stop,now=now,deadline=deadline)
 need(reproduced==source_result,'SOURCE_REPLAY_MISMATCH')
 o=source_result[1];ev=source_result[2];v=source_result[3]
 mechanism=MAPPING[o.bottleneck_type]
 h=make(HypothesisCandidate,hypothesis_id=hypothesis_id,source_bottleneck_id=o.bottleneck_id,target_component=o.component_id,proposed_mechanism=mechanism,expected_effect='TEST_LOCAL_DEFICIENCY_REDUCTION',assumptions=('SOURCE_IS_DIAGNOSTIC','NO_MEASURED_GAIN','PROVENANCE_UNQUALIFIED'),evidence_refs=tuple(sorted(e.evidence_id for e in ev)),source_commitment=digest(source_result))
 evidence=tuple(make(HypothesisEvidence,evidence_id=e.evidence_id,hypothesis_id=hypothesis_id,source_stage='RSI-002',evidence_type='LOCAL_DIAGNOSTIC',provenance_class=e.provenance_class,verification_status='NOT_INDEPENDENTLY_QUALIFIED',supports_or_contradicts='CONTRADICTS' if e.provenance_class=='CONTRADICTED' else 'UNVERIFIED_SUPPORT',source_commitment=e.commitment,limitations=e.limitations) for e in sorted(ev,key=lambda x:x.evidence_id))
 prediction=make(ImprovementPrediction,hypothesis_id=hypothesis_id,target_metric=metric,baseline_reference=baseline,predicted_direction=direction,predicted_magnitude=(),measurement_requirements=('PINNED_BASELINE','MATCHED_UNITS_POPULATION','OFFLINE_CONTROLLED_TEST'),uncertainty_class='NOT_MEASURED',falsification_conditions=('NO_IMPROVEMENT_AGAINST_BASELINE','REGRESSION_ON_RETAINED_CAPABILITIES'))
 proposal=make(ImprovementProposal,proposal_id=proposal_id,hypothesis_id=hypothesis_id,target_component=o.component_id,target_version=snapshot.component_version,change_type=mechanism,change_summary='ADVISORY_TEST_PROPOSAL_ONLY',affected_interfaces=snapshot.interface_commitments,required_evidence=('BASELINE','INDEPENDENT_VERIFICATION','REGRESSION_TESTS'),required_authorizations=('EXTERNAL_INDEPENDENT_HUMAN_APPROVAL',))
 deps=make(ProposalDependency,proposal_id=proposal_id,prerequisite_proposals=(),affected_components=(o.component_id,),inherited_findings=BLOCKERS,compatibility_requirements=('PRESERVE_PREDECESSORS',),unresolved_dependencies=tuple(sorted(set(dependency.upstream_dependencies+dependency.downstream_dependencies))))
 risks=inputs[4]
 risk=make(ProposalRiskAssessment,proposal_id=proposal_id,regression_risks=risks.regression_risks,security_risks=risks.security_risks,authorization_risks=risks.capability_boundary_risks,integration_risks=risks.dependency_risks,evidence_gaps=('INDEPENDENT_PROVENANCE_UNAVAILABLE','BASELINE_NOT_VALIDATED'),rollback_requirements=risks.rollback_requirements)
 contradicted=o.confidence_class=='CONTRADICTED'
 decision='CONTRADICTED' if contradicted else 'RISK_BLOCKED' if risk.security_risks or risk.authorization_risks else 'REQUIRES_EVIDENCE' if not evidence or o.confidence_class=='UNSUPPORTED' else 'BASELINE_REQUIRED' if not baseline else 'INTEGRATION_NOT_QUALIFIED'
 verdict=make(ProposalVerdict,proposal_id=proposal_id,structural_validity=True,hypothesis_qualification='CONTRADICTED' if contradicted else 'PLAUSIBLE_UNVERIFIED' if evidence else 'UNSUPPORTED',evidence_qualification='NOT_INDEPENDENTLY_QUALIFIED',prediction_qualification='UNVERIFIED_BASELINE' if baseline else 'BASELINE_REQUIRED',risk_classification='BLOCKED' if decision=='RISK_BLOCKED' else 'NOT_QUALIFIED',unresolved_findings=BLOCKERS,decision=decision,decision_reasons=('ADVISORY_ONLY','INHERITED_P1_OPEN','NO_INDEPENDENT_PROVENANCE','BASELINE_NOT_VALIDATED'),authorization_flags=tuple((f,False) for f in FLAGS))
 payload=(h,evidence,prediction,proposal,deps,risk,verdict)
 new=make(ProposalState,state_version='state-v1',sequence=sequence,previous_state_commitment=previous.state_commitment,registered_hypotheses=previous.registered_hypotheses+(hypothesis_id,),registered_proposals=previous.registered_proposals+(proposal_id,),rejected_proposals=previous.rejected_proposals+((proposal_id,) if decision in ('CONTRADICTED','RISK_BLOCKED') else ()),cumulative_resource_usage=previous.cumulative_resource_usage+2,budget=previous.budget,history=previous.history+(digest((approved_input,payload)),))
 return new,payload
