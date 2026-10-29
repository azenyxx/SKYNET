import unittest,tempfile
from pathlib import Path
from dataclasses import replace,asdict
from cognitive_research_contracts import *
from cognitive_research_runner import domain
from cognitive_research_registry import Registry
from cognitive_research_adapter import research_cycle
from cognitive_meta_audit import MetaAudit
from meta_test_helpers import budget as meta_budget,trace
from cognitive_memory_store import MemoryStore
from cognitive_memory_contracts import MemoryQueryV1
from cognitive_world_store import WorldStore
from world_test_helpers import model
from test_cognitive_model_planning import setup
from cognitive_model_planning_contracts import ModelPlanningResponseV1
from test_memory_contracts import record
H='0'*64
def budget(sid='session',experiments=4):return ResearchBudgetV1('n',sid,10,(H,),'OBSERVED_SYNTHETIC','TEST_ONLY',4,experiments,4,1000,0)
class Fixture:
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);self.path=str(root/'research');self.r=Registry(self.path,True);self.m=MemoryStore(str(root/'m'),True);self.w=WorldStore(str(root/'w'),True);self.a=MetaAudit(str(root/'a'),True);self.state,self.pr,self.obj=setup()
 def tearDown(self):
  for x in (self.r,self.m,self.w,self.a):x.close()
  self.tmp.cleanup()
 def run_cycle(self,env='A',sid='session',b=None,requested=()):
  return research_cycle(domain(env,session_id=sid),b or budget(sid),self.r,len(self.r.verify()),self.a,self.m,MemoryQueryV1('n','s',2,10,'UNVERIFIED'),self.w,model(),self.state,self.pr,ModelPlanningResponseV1(canonical(self.obj),'fixture',self.pr.request_binding),meta_budget(sid),requested)
