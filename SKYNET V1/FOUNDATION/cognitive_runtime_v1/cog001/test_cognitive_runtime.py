import hashlib
import unittest
from dataclasses import replace, FrozenInstanceError
from unittest.mock import patch
from cognitive_contracts import *
from cognitive_runtime import apply_transition

T='2026-10-15T00:00:00.000000Z'
ID='00000000-0000-0000-0000-000000000001'
def initial():
    return CognitiveStateV1('cog-state-v1',CognitiveTaskV1(ID,'cog-task-v1','echo',T,1,'CREATED',0,TaskBudgetV1('cog-budget-v1',ResourcesV1(2,2,2,10,100),ResourcesV1(0,0,0,0,0)),(),(),None,None),())
def transition(s,k,**kw):
    return TaskTransitionV1('cog-transition-v1',ID,s.task.revision,k,T,kw.get('consumption'),kw.get('step'),kw.get('result'),kw.get('evidence_refs',()),kw.get('reason'))
def advance(s,k,**kw): return apply_transition(s,transition(s,k,**kw))
def running():
    s=initial()
    for k in ('VALIDATE','PLAN','READY','START'): s=advance(s,k)
    return s
def verifying():
    r=TaskResultV1('cog-result-v1','echo',hashlib.sha256(b'echo').hexdigest(),'UNVERIFIED')
    return advance(running(),'SUBMIT',result=r,evidence_refs=(EvidenceRefV1(ID,r.content_hash,ID,ID),))

class RuntimeTests(unittest.TestCase):
    def test_lifecycle(self):
        s=advance(advance(verifying(),'VERIFY_SIMULATED'),'COMPLETE')
        self.assertEqual(s.task.status,'COMPLETED'); self.assertEqual(s.task.revision,7)
        self.assertEqual(s.task.result.verification,'VERIFICATION_SIMULATED')
    def test_invalid(self):
        with self.assertRaises(ContractError): advance(initial(),'START')
    def test_terminal(self):
        for k in ('FAIL','CANCEL'):
            s=advance(initial(),k,reason='test')
            with self.assertRaises(ContractError): advance(s,'VALIDATE')
        s=advance(advance(verifying(),'VERIFY_SIMULATED'),'COMPLETE')
        with self.assertRaises(ContractError): advance(s,'CANCEL',reason='test')
    def test_revision(self): self.assertEqual(advance(initial(),'VALIDATE').task.revision,1)
    def test_stale(self):
        s=running()
        with self.assertRaisesRegex(ContractError,'STALE_REVISION'): apply_transition(s,replace(transition(s,'BLOCK',reason='x'),expected_revision=0))
    def test_events(self):
        from cognitive_events import event_digest
        a=advance(initial(),'VALIDATE'); b=advance(initial(),'VALIDATE')
        self.assertEqual(a,b); self.assertEqual(event_digest(a.events[0]),a.events[0].event_digest)
    def exhaust(self,field):
        s=running(); values=dict(steps=0,tool_calls=0,model_calls=0,tokens=0,time_ms=0)
        if field=='steps':
            for n in range(2):
                s=advance(s,'CONSUME',consumption=ResourcesV1(1,0,0,0,0),step=TaskStepV1('cog-step-v1',f'00000000-0000-0000-0000-{n+2:012d}','test'))
            values['steps']=1
            step=TaskStepV1('cog-step-v1','00000000-0000-0000-0000-000000000004','test')
        else:
            values[field]=getattr(s.task.budget.maximum,field)+1; step=None
        out=advance(s,'CONSUME',consumption=ResourcesV1(**values),step=step)
        self.assertEqual(out.task.status,'BLOCKED'); self.assertEqual(out.task.budget,s.task.budget)
    def test_steps(self): self.exhaust('steps')
    def test_tools(self): self.exhaust('tool_calls')
    def test_models(self): self.exhaust('model_calls')
    def test_tokens(self): self.exhaust('tokens')
    def test_time(self): self.exhaust('time_ms')
    def test_no_reset(self):
        s=advance(running(),'CONSUME',consumption=ResourcesV1(0,1,1,2,3))
        self.assertEqual(advance(s,'BLOCK',reason='x').task.budget,s.task.budget)
    def test_failure(self): self.assertEqual(advance(running(),'FAIL',reason='x').task.status,'FAILED')
    def test_cancel(self): self.assertEqual(advance(running(),'CANCEL',reason='x').task.status,'CANCELLED')
    def test_block(self): self.assertEqual(advance(initial(),'BLOCK',reason='x').task.status,'BLOCKED')
    def test_verification_required(self):
        with self.assertRaisesRegex(ContractError,'VERIFICATION_REQUIRED'): advance(verifying(),'COMPLETE')
    def test_no_trusted(self):
        s=verifying()
        with self.assertRaisesRegex(ContractError,'TRUST_BOUNDARY'): replace(s.task,result=replace(s.task.result,verification='VERIFICATION_TRUSTED'))
    def test_no_mutation(self):
        s=running(); old=canonical_bytes(s); advance(s,'CONSUME',consumption=ResourcesV1(0,1,0,0,0)); self.assertEqual(old,canonical_bytes(s))
        with self.assertRaises(FrozenInstanceError): s.task.revision=20
    def test_no_io(self):
        s=initial(); t=transition(s,'VALIDATE')
        with patch('builtins.open',side_effect=AssertionError),patch('socket.socket',side_effect=AssertionError),patch('time.time',side_effect=AssertionError):
            self.assertEqual(apply_transition(s,t).task.status,'VALIDATED')
    def test_wrong_target(self):
        s=initial()
        with self.assertRaisesRegex(ContractError,'TARGET'): apply_transition(s,replace(transition(s,'VALIDATE'),task_id='00000000-0000-0000-0000-000000000002'))
    def test_no_auth_from_reference(self):
        r=TaskResultV1('cog-result-v1','wrong',hashlib.sha256(b'wrong').hexdigest(),'UNVERIFIED')
        s=advance(running(),'SUBMIT',result=r,evidence_refs=(EvidenceRefV1(ID,r.content_hash,ID,ID),))
        with self.assertRaisesRegex(ContractError,'SIMULATED_VERIFICATION_FAILED'): advance(s,'VERIFY_SIMULATED')
    def test_time_regression(self):
        s=initial()
        with self.assertRaisesRegex(ContractError,'TIME_REGRESSION'): apply_transition(s,replace(transition(s,'VALIDATE'),timestamp='2026-10-14T00:00:00.000000Z'))
    def test_overflow(self):
        s=running(); s=initial(); s=replace(s,task=replace(s.task,budget=TaskBudgetV1('cog-budget-v1',ResourcesV1(2,MAX,2,10,100),ResourcesV1(0,0,0,0,0))))
        for k in ('VALIDATE','PLAN','READY','START'): s=advance(s,k)
        s=advance(s,'CONSUME',consumption=ResourcesV1(0,MAX,0,0,0))
        with self.assertRaisesRegex(ContractError,'INTEGER_OVERFLOW'): advance(s,'CONSUME',consumption=ResourcesV1(0,1,0,0,0))
