from cognitive_parallel_contracts import *
from cognitive_parallel_operators import inputs
from cognitive_planner import construct_plan,initial_progress,ready_steps
from cognitive_model_planning import validate_model_plan

def bind_plan(plan,namespace,workload_id,bindings,workers=2,timeout_ms=500,queue_capacity=16):
 plan.__post_init__();require(type(bindings) is tuple and len(bindings)==len(plan.steps),'BINDINGS');require(all(type(x) is tuple and len(x)==3 for x in bindings),'BINDING_TYPE');by={x[0]:x[1:] for x in bindings};require(len(by)==len(bindings) and set(by)=={s.step_id for s in plan.steps},'STEP_BINDING');tasks=[]
 for s in plan.steps:
  require(s.max_retries==0,'RETRIES_DISABLED');op,payload=by[s.step_id];task=ParallelTaskV1(s.step_id,s.dependencies,0,op,payload,digest('Input',dict(operation=op,payload=payload)));inputs(task);tasks.append(task)
 return WorkloadV1(namespace,workload_id,plan.plan_id,tuple(tasks),workers,queue_capacity,timeout_ms,len(tasks))
def prepare(state,steps,namespace,workload_id,bindings,**limits):
 plan=construct_plan(state,steps);return plan,bind_plan(plan,namespace,workload_id,bindings,**limits)
def prepare_model(state,request,response,namespace,workload_id,bindings,**limits):
 result=validate_model_plan(state,request,response);require(result.status=='MODEL_PLAN_ACCEPTED_ISOLATED','PLANNER_REJECTED');return result.validated_plan,bind_plan(result.validated_plan,namespace,workload_id,bindings,**limits)
