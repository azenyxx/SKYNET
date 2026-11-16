from rsi_test_helpers import *
from research_test_helpers import Fixture,meta_budget
from transfer_test_helpers import session as transfer_session
from cognitive_transfer_registry import TransferRegistry
from cognitive_rsi_adapter import improvement_cycle
from cognitive_memory_contracts import MemoryQueryV1
from cognitive_model_planning_contracts import ModelPlanningResponseV1
from world_test_helpers import model
class Integration(Fixture,unittest.TestCase):
 def run_rsi(self,invalid=False):
  self.run_cycle();t=TransferRegistry(str(Path(self.tmp.name)/'t'),True);t.append(transfer_session(),0);r=ImprovementRegistry(str(Path(self.tmp.name)/'rsi'),True)
  try:return improvement_cycle('n','rsi','RESOURCE',r,0,self.a,self.r,t,self.m,MemoryQueryV1('n','s',2,10,'UNVERIFIED'),self.w,model(),self.state,self.pr,ModelPlanningResponseV1(b'{}' if invalid else canonical(self.obj),'fixture',self.pr.request_binding),meta_budget('rsi'))
  finally:r.close();t.close()
 def test_original_chain(self):self.assertEqual(self.run_rsi().decision.action,'RECOMMEND_FOR_HUMAN_REVIEW')
 def test_planner_stop(self):
  with self.assertRaises(RSIError):self.run_rsi(True)
