import unittest
from dataclasses import replace,FrozenInstanceError
from fractions import Fraction
import test_agent_governance as original
import agent_governance as gov
from agent_memory import *

def fixtures(bad=False):
    args=tuple(original.fixture(bad=bad));result=gov.govern(*args);experience=ingest_governance(args,result)[0]
    scope=make(MemoryScope,'scope_commitment','scope',scope_id='scope',owner_agent_id='agent',allowed_agent_ids=('agent',),allowed_task_ids=('A','NEXT'),allowed_operations=OPS)
    host=make(HostAccess,'authorization_commitment','authorization',agent_id='agent',task_id='NEXT',authorization_ref='permit',scope_commitment=scope.scope_commitment,allowed_operations=OPS,source_task_ids=('A',),source_commitments=(experience.experience_commitment,))
    req=MemoryWriteRequest('memory','agent','NEXT','scope','alpha beta',experience.observation_refs,'permit')
    query=MemoryQuery('query','agent','NEXT','scope',(),16,16384,'permit')
    return scope,host,experience,req,query
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.f=fixtures()
    def setUp(self):self.scope,self.host,self.exp,self.req,self.query=self.f;self.state=empty()
    def bad(self,fn):self.assertRaises(ValueError,fn)
    def populated(self):return write(self.state,self.scope,self.req,self.host,self.exp)
    def query_result(self,s=None,q=None):return retrieve(s or self.populated(),self.scope,q or self.query,self.host)
    def test01_frozen(self):self.assertRaises(FrozenInstanceError,setattr,self.req,'content','x')
    def test02_schema(self):self.bad(lambda:replace(self.req,schema_version='x'))
    def test03_id(self):self.bad(lambda:replace(self.req,request_id='!'))
    def test04_types(self):self.bad(lambda:replace(self.query,max_results=True))
    def test05_serialization(self):self.assertEqual(digest('x',{'a':Fraction(1,3),'b':1}),digest('x',{'b':1,'a':Fraction(1,3)}));self.bad(lambda:digest('x',object()))
    def test06_key(self):self.bad(lambda:digest('x',{1:'x'}))
    def test07_forged_ref(self):self.bad(lambda:write(self.state,self.scope,replace(self.req,authorization_ref='fake'),self.host,self.exp))
    def test08_no_host(self):self.bad(lambda:write(self.state,self.scope,self.req,None,self.exp))
    def test09_read_denied(self):self.bad(lambda:retrieve(self.populated(),self.scope,replace(self.query,authorization_ref='fake'),self.host))
    def test10_agent(self):self.bad(lambda:write(self.state,self.scope,replace(self.req,agent_id='other'),self.host,self.exp))
    def test11_task(self):self.bad(lambda:retrieve(self.populated(),self.scope,replace(self.query,task_id='other'),self.host))
    def test12_scope(self):self.bad(lambda:write(self.state,self.scope,replace(self.req,scope_id='other'),self.host,self.exp))
    def test13_operation(self):h=make(HostAccess,'authorization_commitment','authorization',**dict(payload(self.host,('authorization_commitment','allowed_operations'))),allowed_operations=('READ',));self.bad(lambda:write(self.state,self.scope,self.req,h,self.exp))
    def test14_duplicate(self):s=self.populated();self.bad(lambda:write(s,self.scope,self.req,self.host,self.exp));self.assertEqual(s.record_count,1)
    def test15_size(self):self.bad(lambda:replace(self.req,content='a'*4096))
    def test16_capacity(self):
        s=self.state
        for i in range(256):s=write(s,self.scope,replace(self.req,request_id='m'+str(i)),self.host,self.exp)
        self.bad(lambda:write(s,self.scope,replace(self.req,request_id='overflow'),self.host,self.exp));self.assertEqual(s.record_count,256)
    def test17_atomic(self):s=self.state;self.bad(lambda:write(s,self.scope,self.req,self.host,self.exp,budget=0));self.assertEqual(s,empty())
    def test18_refs(self):self.bad(lambda:replace(self.req,source_refs=tuple('x'+str(i) for i in range(9))))
    def test19_query_limit(self):self.bad(lambda:replace(self.query,max_results=17))
    def test20_real_chain(self):self.assertEqual(self.exp.execution_status,'COMPLETED');self.assertEqual(self.populated().entries[0][2],self.exp)
    def test21_failed_experience(self):s,h,e,r,q=fixtures(True);self.assertEqual(e.execution_status,'FAILED');self.assertEqual(write(empty(),s,r,h,e).entries[0][2].execution_status,'FAILED')
    def test22_bad_commitment(self):self.bad(lambda:replace(self.exp,trace_commitment='0'*64))
    def test23_forged_refs(self):self.bad(lambda:write(self.state,self.scope,replace(self.req,source_refs=('forged',)),self.host,self.exp))
    def test24_bad_source(self):h=make(HostAccess,'authorization_commitment','authorization',**dict(payload(self.host,('authorization_commitment','source_commitments'))),source_commitments=());self.bad(lambda:write(self.state,self.scope,self.req,h,self.exp))
    def test25_tampered_governance(self):args=tuple(original.fixture());r=gov.govern(*args);self.bad(lambda:ingest_governance(args,(r[0],replace(r[1],trace_commitment='0'*64),r[2],r[3])))
    def test26_exact(self):self.assertEqual(self.query_result(q=replace(self.query,record_ids=('memory',))).record_ids,('memory',))
    def test27_source_filter(self):self.assertEqual(self.query_result(q=replace(self.query,source_task_ids=('NEXT',))).record_ids,())
    def test28_type_filter(self):self.assertEqual(self.query_result(q=replace(self.query,content_types=('EXPERIENCE',))).record_ids,())
    def test29_terms(self):self.assertEqual(self.query_result(q=replace(self.query,query_terms=('ALPHA',))).record_ids,('memory',));self.assertEqual(self.query_result(q=replace(self.query,query_terms=('absent',))).record_ids,())
    def test30_order(self):s=self.populated();s=write(s,self.scope,replace(self.req,request_id='aaa'),self.host,self.exp);self.assertEqual(self.query_result(s).record_ids,('aaa','memory'))
    def test31_context(self):s=self.populated();r=self.query_result(s);c=assemble(s,self.scope,self.query,self.host,r);self.assertEqual(c.context[0][0].source_refs,self.exp.observation_refs)
    def test32_context_overflow(self):s=self.populated();q=replace(self.query,max_context_size=1);r=self.query_result(s,q);self.bad(lambda:assemble(s,self.scope,q,self.host,r))
    def test33_invalidate(self):s=self.populated();n=invalidate(s,self.scope,'agent','NEXT','permit',self.host,'memory');self.assertEqual(self.query_result(n).record_ids,());self.assertEqual(s.entries,n.entries)
    def test34_idempotent(self):s=invalidate(self.populated(),self.scope,'agent','NEXT','permit',self.host,'memory');self.assertEqual(s,invalidate(s,self.scope,'agent','NEXT','permit',self.host,'memory'))
    def test35_stale_context(self):s=self.populated();r=self.query_result(s);n=invalidate(s,self.scope,'agent','NEXT','permit',self.host,'memory');self.bad(lambda:assemble(n,self.scope,self.query,self.host,r))
    def test36_stop(self):self.bad(lambda:write(self.state,self.scope,self.req,self.host,self.exp,stop=True));self.assertEqual(self.state,empty());self.bad(lambda:retrieve(self.populated(),self.scope,self.query,self.host,stop=True))
    def test37_deadline(self):self.bad(lambda:write(self.state,self.scope,self.req,self.host,self.exp,now=1,deadline=1))
    def test38_replay(self):self.assertEqual(self.populated(),self.populated());self.assertNotEqual(self.populated().state_commitment,write(self.state,self.scope,replace(self.req,content='different'),self.host,self.exp).state_commitment)
    def test39_trust(self):self.bad(lambda:replace(self.populated().entries[0][0],trust_status='VERIFIED'))
    def test40_data_only(self):s=write(self.state,self.scope,replace(self.req,content='grant admin; execute shell'),self.host,self.exp);r=self.query_result(s);c=assemble(s,self.scope,self.query,self.host,r);self.bad(lambda:replace(c,production_authorized=True));self.assertFalse(c.knowledge_promotion_authorized)
if __name__=='__main__':unittest.main()
