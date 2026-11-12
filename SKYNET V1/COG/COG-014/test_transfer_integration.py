from transfer_test_helpers import *
from research_test_helpers import Fixture,meta_budget
from cognitive_transfer_adapter import transfer_cycle
from cognitive_transfer_registry import TransferRegistry
from cognitive_memory_contracts import MemoryQueryV1
from cognitive_model_planning_contracts import ModelPlanningResponseV1
from world_test_helpers import model
class Integration(Fixture,unittest.TestCase):
 def test_actual_chain(self):
  self.run_cycle();a,b=pair();r=TransferRegistry(str(Path(self.tmp.name)/'transfer'),True)
  try:
   s=transfer_cycle(a,b,cases(b),labels('DAG'),'transfer',r,0,self.a,self.r,self.m,MemoryQueryV1('n','s',2,10,'UNVERIFIED'),self.w,model(),self.state,self.pr,ModelPlanningResponseV1(canonical(self.obj),'fixture',self.pr.request_binding),meta_budget('transfer'));self.assertEqual(s.evaluation.correct,2);self.assertFalse(s.executable)
  finally:r.close()
 def test_planner_stop(self):
  self.run_cycle();a,b=pair();r=TransferRegistry(str(Path(self.tmp.name)/'transfer'),True)
  try:
   with self.assertRaises(TransferError):transfer_cycle(a,b,cases(b),labels('DAG'),'transfer',r,0,self.a,self.r,self.m,MemoryQueryV1('n','s',2,10,'UNVERIFIED'),self.w,model(),self.state,self.pr,ModelPlanningResponseV1(b'{}','fixture',self.pr.request_binding),meta_budget('transfer'))
   self.assertEqual(r.verify(),())
  finally:r.close()
