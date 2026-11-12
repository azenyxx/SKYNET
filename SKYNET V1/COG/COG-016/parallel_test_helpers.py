import unittest,tempfile
from pathlib import Path
from dataclasses import replace
from cognitive_parallel_contracts import *
from cognitive_parallel_adapter import prepare,prepare_model
from cognitive_parallel_registry import ParallelRegistry
from cognitive_parallel_supervisor import run
from cognitive_parallel_verification import verify,aggregate
from cognitive_parallel_operators import execute
from test_cognitive_planner import fixture
from cognitive_plan_contracts import PlanStepV1
from cognitive_contracts import ResourcesV1

def setup(n=2,dependent=False,workers=2,timeout=500):
 state,_=fixture();ids=tuple('00000000-0000-0000-0000-'+str(i+1).zfill(12) for i in range(n));steps=tuple(PlanStepV1('cog-plan-step-v1',x,'ANALYZE',(ids[i-1],) if dependent and i else (),ResourcesV1(1,0,0,0,0),0,'PENDING',0) for i,x in enumerate(ids));bindings=tuple((x,'SUM_SQUARES_V1','2,3,4') for x in ids);return prepare(state,steps,'n','work',bindings,workers=workers,timeout_ms=timeout)
class Fixture:
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'r');self.r=ParallelRegistry(self.path,True)
 def tearDown(self):self.r.close();self.tmp.cleanup()
 def create(self,**kw):
  p,w=setup(**kw);self.r.change('n','work',0,'CREATE',workload=w);return p,w
