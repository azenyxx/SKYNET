from parallel_test_helpers import *
from test_cognitive_model_planning import setup as model_setup
from cognitive_model_planning_contracts import ModelPlanningResponseV1
class Integration(unittest.TestCase):
 def test_actual_model_plan(self):
  state,req,obj=model_setup();bindings=tuple((s['step_id'],'SHA256_TEXT_V1','test') for s in obj['steps']);p,w=prepare_model(state,req,ModelPlanningResponseV1(canonical(obj),'fixture',req.request_binding),'n','model',bindings)
  with tempfile.TemporaryDirectory() as d:
   r=ParallelRegistry(str(Path(d)/'r'),True);r.change('n','model',0,'CREATE',workload=w);o,stats=run(p,w,r);self.assertEqual(o.status,'COMPLETE_ISOLATED');r.close()
 def test_model_rejection(self):
  state,req,obj=model_setup()
  with self.assertRaises(ValueError):prepare_model(state,req,ModelPlanningResponseV1(b'{}','fixture',req.request_binding),'n','model',())
 def test_original_cycle_rejection(self):
  from cognitive_planner import construct_plan
  state,(a,b)=fixture()
  with self.assertRaises(ValueError):construct_plan(state,(replace(a,dependencies=(b.step_id,)),b))
 def test_no_predecessor_mutation(self):
  from cognitive_contracts import canonical_bytes
  state,steps=fixture();before=canonical_bytes(state)
  from cognitive_planner import construct_plan
  construct_plan(state,steps);self.assertEqual(canonical_bytes(state),before)
