import unittest
from dataclasses import replace
import agent_collaboration as c
import test_agent_governance as fixture
import agent_governance as gov
m=c.m

def setup():
    args=tuple(fixture.fixture());result=gov.govern(*args);e=c.memory.ingest_governance(args,result)[0]
    scope=m.make(m.MemoryScope,'scope_commitment','scope',scope_id='scope',owner_agent_id='agent',allowed_agent_ids=('agent','receiver'),allowed_task_ids=(e.task_id,),allowed_operations=('READ','WRITE','INVALIDATE'))
    def access(agent):return m.make(m.HostAccess,'authorization_commitment','authorization',agent_id=agent,task_id=e.task_id,authorization_ref='auth:'+agent,scope_commitment=scope.scope_commitment,allowed_operations=('READ','WRITE','INVALIDATE'),source_task_ids=(e.task_id,),source_commitments=(e.experience_commitment,))
    a=access('agent');b=access('receiver');w=m.MemoryWriteRequest('memory','agent',e.task_id,'scope','diagnostic',e.observation_refs,a.authorization_ref)
    store=c.memory.write(c.memory.empty(),scope,w,a,e)
    s=c.seal(c.CollaborationSession,session_id='session',owner_id='owner',participant_agent_ids=('agent','receiver'),authorized_task_ids=(e.task_id,),session_budget=8)
    g=c.seal(c.CollaborationGrant,grant_id='grant',issuer_id='owner',sender_agent_id='agent',recipient_agent_id='receiver',allowed_task_ids=(e.task_id,),allowed_memory_refs=('memory',),allowed_operations=('TRANSFER',),max_messages=8)
    h=c.HostPolicy(s.session_commitment,(g.grant_commitment,),store.state_commitment,(a.authorization_commitment,b.authorization_commitment),c.initial(s).state_commitment)
    msg=c.AgentMessage('msg','session','agent','receiver',e.task_id,1,m.digest('content','diagnostic'),('memory',))
    return [s,g,h,store,scope,a,b,((msg,'diagnostic'),)]
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=setup()
    def run_case(self,**kw):return c.exchange(*self.base,previous=c.initial(self.base[0]),**kw)
    def bad_message(self,**kw):
        args=self.base.copy();args[-1]=((replace(args[-1][0][0],**kw),'diagnostic'),)
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))
    def test01_real_pipeline(self):self.assertEqual(self.run_case()[2].execution_status,'DIAGNOSTIC_DELIVERED')
    def test02_provenance(self):self.assertEqual(self.run_case()[3][0].context[0],self.base[3].entries[0])
    def test03_no_mutation(self):before=m.encoded(self.base[3]);self.run_case();self.assertEqual(before,m.encoded(self.base[3]))
    def test04_deterministic(self):self.assertEqual(self.run_case(),self.run_case())
    def test05_budget(self):s=self.run_case()[0];self.assertEqual((s.consumed_budget,s.remaining_budget),(1,7))
    def test06_stop(self):
        with self.assertRaises(ValueError):self.run_case(stop=True)
    def test07_deadline(self):
        with self.assertRaises(ValueError):self.run_case(now=1,deadline=1)
    def test08_sender(self):self.bad_message(sender_agent_id='intruder')
    def test09_recipient(self):self.bad_message(recipient_agent_id='intruder')
    def test10_sequence(self):self.bad_message(sequence_number=2)
    def test11_source(self):self.bad_message(source_refs=('other',))
    def test12_task(self):self.bad_message(source_task_id='other')
    def test13_payload(self):self.bad_message(payload_commitment='0'*64)
    def test14_promotion(self):
        with self.assertRaises(ValueError):replace(self.base[-1][0][0],trust_status='VERIFIED')
    def test15_duplicate(self):
        args=self.base.copy();args[-1]=args[-1]*2
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))
    def test16_forged_host_grant(self):
        args=self.base.copy();args[2]=replace(args[2],grant_commitments=())
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))
    def test17_stale(self):
        args=self.base.copy();args[2]=replace(args[2],memory_state_commitment='0'*64)
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))
    def test18_invalidated(self):
        args=self.base.copy();a=args[5];args[3]=c.memory.invalidate(args[3],args[4],a.agent_id,a.task_id,a.authorization_ref,a,'memory');args[2]=replace(args[2],memory_state_commitment=args[3].state_commitment)
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))
    def test19_access(self):
        args=self.base.copy();args[2]=replace(args[2],access_commitments=(args[5].authorization_commitment,))
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))
    def test20_authority_false(self):self.assertIs(self.run_case()[2].production_authorized,False)
    def test21_knowledge_false(self):self.assertIs(self.run_case()[2].knowledge_promotion_authorized,False)
    def test22_handoff_closed(self):
        with self.assertRaisesRegex(ValueError,'DENIED'):c.handoff()
    def test23_version(self):
        with self.assertRaises(ValueError):replace(self.base[0],schema_version='v2')
    def test24_negative(self):
        with self.assertRaises(ValueError):replace(self.base[0],session_budget=-1)
    def test25_bad_commitment(self):
        with self.assertRaises(ValueError):replace(self.base[0],session_commitment='0'*64)
    def test26_duplicate_participant(self):
        with self.assertRaises(ValueError):replace(self.base[0],participant_agent_ids=('agent','agent'))
    def test27_oversize(self):
        args=self.base.copy();args[-1]=((args[-1][0][0],'x'*4097),)
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))
    def test28_replay_changed(self):self.assertFalse(c.replay_equal(self.run_case(),self.run_case()[:3]))
    def test29_message_limit(self):
        args=self.base.copy();args[-1]=args[-1]*65
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))
    def test30_zero_budget(self):
        args=self.base.copy();args[0]=c.seal(c.CollaborationSession,session_id='session',owner_id='owner',participant_agent_ids=('agent','receiver'),authorized_task_ids=args[0].authorized_task_ids,session_budget=0);args[2]=replace(args[2],session_commitment=args[0].session_commitment)
        with self.assertRaises(ValueError):c.exchange(*args,previous=c.initial(args[0]))


def continued(base,state,msg_id='next',sequence=2):
    args=base.copy();args[2]=replace(args[2],expected_state=state.state_commitment);args[-1]=((replace(args[-1][0][0],message_id=msg_id,sequence_number=sequence),'diagnostic'),);return args

def handoff_fixture(base,task='A',statuses=None):
    source=tuple(fixture.fixture()[:7]);target=list(source)
    identity=gov.ac.AgentIdentity('receiver','local',gov.ac.OPS);bundles=[];tasks=[];delegations=[];parents=[]
    for st,b,d in zip(source[2],source[6],source[3]):
        t=replace(b[1],agent_id='receiver');g=replace(b[4][0],agent_id='receiver',task_commitment=gov.ac.digest('task',t));parents.append(g)
        tasks.append(replace(st,agent_id='receiver',task_commitment=g.task_commitment));delegations.append(replace(d,delegate_agent_id='receiver'));bundles.append((identity,t,b[2],b[3],(g,),b[5]))
    target[2]=tuple(tasks);target[3]=tuple(delegations);target[4]=replace(source[4],delegation_commitments=tuple(gov.digest(d) for d in delegations),parent_authorizations=tuple(parents),approved_agent_ids=('receiver',));target[5]=(gov.oc.SupervisedAgent('receiver',gov.oc.digest(identity),tuple(t.task_id for t in tasks)),);target[6]=tuple(bundles);target=tuple(target)
    statuses=statuses or tuple((t.task_id,'READY') for t in source[2])
    req=c.seal(c.TaskHandoff,handoff_id='handoff',source_agent_id='agent',target_agent_id='receiver',task_id=task,parent_authorization_ref='grant:'+task,handoff_status='READY')
    session=c.seal(c.CollaborationSession,session_id='session',owner_id='owner',participant_agent_ids=('agent','receiver'),authorized_task_ids=tuple(t.task_id for t in source[2]),session_budget=8)
    state=c.initial(session);host=replace(base[2],session_commitment=session.session_commitment,expected_state=state.state_commitment,handoff_approvals=(c.digest((req,source,target,statuses)),))
    return [session,host,state,req,source,target,statuses]
class StatefulTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=setup()
    def first(self):return c.exchange(*self.base,previous=c.initial(self.base[0]))[0]
    def test31_two_calls(self):
        state=self.first();args=continued(self.base,state);out=c.exchange(*args,previous=state);self.assertEqual(out[0].ordered_message_ids,('msg','next'));self.assertEqual(out[0].consumed_budget,2)
    def test32_duplicate_across(self):
        state=self.first();args=continued(self.base,state,'msg')
        with self.assertRaisesRegex(ValueError,'DUPLICATE_MESSAGE'):c.exchange(*args,previous=state)
    def test33_stale(self):
        state=self.first();args=continued(self.base,state)
        with self.assertRaisesRegex(ValueError,'STALE_OR_FORGED_STATE'):c.exchange(*args,previous=c.initial(args[0]))
    def test34_forged(self):
        state=self.first();args=continued(self.base,state);kw={f.name:getattr(state,f.name) for f in c.fields(state) if f.name!='state_commitment'};kw['remaining_budget']=8;forged=c.seal(c.CollaborationState,**kw)
        with self.assertRaises(ValueError):c.exchange(*args,previous=forged)
    def test35_sequence_rollback(self):
        state=self.first();args=continued(self.base,state,sequence=1)
        with self.assertRaisesRegex(ValueError,'SEQUENCE'):c.exchange(*args,previous=state)
    def test36_exhaustion(self):
        state=c.initial(self.base[0])
        for i in range(1,9):state=c.exchange(*continued(self.base,state,'m'+str(i),i),previous=state)[0]
        self.assertEqual(state.remaining_budget,0)
        with self.assertRaises(ValueError):c.exchange(*continued(self.base,state,'m9',9),previous=state)
    def test37_atomic_rejection(self):
        state=self.first();before=m.encoded(state);args=continued(self.base,state);args[-1]=args[-1]+args[-1]
        with self.assertRaises(ValueError):c.exchange(*args,previous=state)
        self.assertEqual(before,m.encoded(state))
    def test38_stop_between(self):
        state=self.first()
        with self.assertRaisesRegex(ValueError,'STOPPED'):c.exchange(*continued(self.base,state),previous=state,stop=True)
    def test39_handoff_success(self):
        a=handoff_fixture(self.base);out=c.handoff(*a);self.assertEqual(out[0].assignments[0][:3],('A','agent','receiver'));self.assertEqual(out[0].remaining_budget,7)
    def test40_handoff_unauthorized(self):
        a=handoff_fixture(self.base);a[1]=replace(a[1],handoff_approvals=())
        with self.assertRaisesRegex(ValueError,'DENIED'):c.handoff(*a)
    def test41_duplicate_handoff(self):
        a=handoff_fixture(self.base);a[2]=c.handoff(*a)[0];a[1]=replace(a[1],expected_state=a[2].state_commitment)
        with self.assertRaisesRegex(ValueError,'ALREADY_ASSIGNED'):c.handoff(*a)
    def test42_failed_dependency(self):
        statuses=(('A','FAILED'),('B','READY'),('C','READY'),('E','READY'),('F','READY'));a=handoff_fixture(self.base,'B',statuses)
        with self.assertRaisesRegex(ValueError,'FAILED_DEPENDENCY'):c.handoff(*a)
    def test43_pending_dependency(self):
        with self.assertRaisesRegex(ValueError,'BLOCKED_DEPENDENCY'):c.handoff(*handoff_fixture(self.base,'B'))
    def test44_missing_dependency(self):
        a=handoff_fixture(self.base);source=list(a[4]);source[2]=(replace(source[2][0],dependencies=('missing',)),)+source[2][1:];a[4]=tuple(source);a[1]=replace(a[1],handoff_approvals=(c.digest(tuple(a[3:])),))
        with self.assertRaises(ValueError):c.handoff(*a)
    def test45_capability_escalation(self):
        a=handoff_fixture(self.base);target=list(a[5]);target[4]=replace(target[4],parent_capabilities=());a[5]=tuple(target);a[1]=replace(a[1],handoff_approvals=(c.digest(tuple(a[3:])),))
        with self.assertRaises(ValueError):c.handoff(*a)
    def test46_target_forgery(self):
        a=handoff_fixture(self.base);a[3]=c.seal(c.TaskHandoff,handoff_id='handoff',source_agent_id='agent',target_agent_id='intruder',task_id='A',parent_authorization_ref='grant:A',handoff_status='READY')
        with self.assertRaises(ValueError):c.handoff(*a)
    def test47_history(self):
        state=self.first();out=c.exchange(*continued(self.base,state),previous=state);self.assertEqual(out[1].ordered_events[0][0],state.state_commitment);self.assertEqual(out[1].ordered_events[0][-1],out[0].state_commitment)
    def test48_changed_authorization(self):
        state=self.first();a=continued(self.base,state);b=a.copy();b[2]=replace(b[2],handoff_approvals=('0'*64,));self.assertNotEqual(c.exchange(*a,previous=state)[0].state_commitment,c.exchange(*b,previous=state)[0].state_commitment)
    def test49_cycle(self):
        a=handoff_fixture(self.base);source=list(a[4]);source[2]=(replace(source[2][0],dependencies=('C',)),)+source[2][1:];a[4]=tuple(source);a[1]=replace(a[1],handoff_approvals=(c.digest(tuple(a[3:])),))
        with self.assertRaisesRegex(ValueError,'CYCLE'):c.handoff(*a)
    def test50_real_combined(self):
        a=handoff_fixture(self.base);args=self.base.copy();args[0]=a[0];args[2]=a[1];state=c.exchange(*args,previous=a[2])[0];args=continued(args,state);state=c.exchange(*args,previous=state)[0];a[2]=state;a[1]=replace(a[1],expected_state=state.state_commitment);result=c.handoff(*a);self.assertEqual(result[0].consumed_budget,3);self.assertEqual(result[0].remaining_budget,5)
if __name__=='__main__':unittest.main()
