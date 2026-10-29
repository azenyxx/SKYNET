"""One bounded read-only replay. No production, persistence or adoption."""
from integrated_qualification_contracts import *
import rollback_safety_engine as predecessor

def policy():return make(QualificationPolicy,policy_version='v1',mandatory_capabilities=CAPS,evidence_requirements=('ORIGINAL_REPLAY',),integration_requirements=STAGES,finding_rules='PRESERVE_ALL_NONEXHAUSTIVE',authorization_constraints=tuple((f,False) for f in FLAGS),resource_limits=7,prohibited_operations=('EXECUTION','ADOPTION','TRAINING','DEPLOYMENT','ACTUAL_ROLLBACK'))
def initial():return make(QualificationState,state_version='v1',sequence=0,previous_state_commitment='0'*64,assessed_stages=(),assessed_capabilities=(),unresolved_findings=FINDINGS,cumulative_resource_usage=0,state_commitment=digest(('initial',FINDINGS)))
def qualify(records,call,expected_result,policy,previous,*,state_pin,input_pin,sequence,stop=False,now=0,deadline=1):
 check(policy,QualificationPolicy);check(previous,QualificationState)
 need(type(records) is tuple and len(records)==7,'STAGES')
 for r in records:check(r,StageQualificationRecord)
 ids=tuple(r.stage_id for r in records);need(len(set(ids))==7,'DUPLICATE');need(tuple(sorted(ids))==STAGES,'STAGES')
 need(state_pin==previous.commitment,'STATE_PIN');need(previous.sequence==0 and type(sequence) is int and sequence==1,'REPLAY')
 need(input_pin==digest((tuple(sorted(records,key=lambda r:r.stage_id)),call,expected_result,policy)),'INPUT_PIN')
 need(type(stop) is bool and type(now) is int and type(deadline) is int,'CONTROL');need(not stop,'STOPPED');need(now<deadline,'DEADLINE');need(policy.resource_limits-previous.cumulative_resource_usage>=7,'OPERATION_BUDGET')
 need(type(call) is tuple and len(call)==10,'SOURCE')
 actual=predecessor.validate(*call,expected_state=call[-1].state_commitment,approved_input=v.digest(call[:-1]),sequence=call[-1].sequence+1)
 need(actual==expected_result,'RESULT_BINDING')
 need(all(flag is False for _,flag in actual[2].authorization_flags),'AUTHORITY')
 need(actual[2].unresolved_findings==v.BLOCKERS,'FINDINGS')
 failed=any(r.observed_test_results[1] or r.observed_test_results[2] for r in records)
 status='SERIES_FAILED' if failed else 'SERIES_BLOCKED' if any(r.integration_class=='NOT_TESTED' for r in records) else 'SERIES_CLOSED_PARTIAL'
 caps=tuple((c,'BLOCKED' if c=='autonomous_rsi' else 'FIXTURE_BASED_ONLY') for c in CAPS)
 verdict=make(IntegratedQualificationVerdict,qualification_id='qualification',stage_results=tuple((r.stage_id,r.reported_status) for r in sorted(records,key=lambda r:r.stage_id)),integration_result='FIXTURE_BASED_ONLY',capability_results=caps,evidence_qualification='NOT_INDEPENDENTLY_QUALIFIED',safety_status='NO_AUTHORIZATION',unresolved_findings=FINDINGS,series_status=status,decision_reasons=('OPEN_FINDINGS','SYNTHETIC_FIXTURES','INVENTORY_NOT_EXHAUSTIVE'),authorization_flags=tuple((f,False) for f in FLAGS))
 state=make(QualificationState,state_version='v1',sequence=1,previous_state_commitment=previous.commitment,assessed_stages=STAGES,assessed_capabilities=CAPS,unresolved_findings=FINDINGS,cumulative_resource_usage=7,state_commitment=digest((previous.commitment,input_pin,verdict.commitment)))
 return state,verdict
