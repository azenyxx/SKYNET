import hashlib
from cognitive_parallel_contracts import *
from cognitive_parallel_operators import inputs

def verify(task,result):
 require(type(result) is WorkerResultV1,'RESULT_TYPE');result.__post_init__();require(result.task_commitment==task.commitment,'RESULT_BINDING');v=inputs(task)
 if task.operation=='SHA256_TEXT_V1':expected=hashlib.sha256(v).hexdigest()
 elif task.operation=='SUM_SQUARES_V1':expected=str(sum(pow(n,2) for n in v))
 else:
  order=v['order'];valid=len(order)==len(v['nodes']) and len(set(order))==len(order) and set(order)==set(v['nodes'])
  if valid:
   seen=set()
   for node in order:
    if any(a not in seen for a,b in v['edges'] if b==node):valid=False;break
    seen.add(node)
  expected='VALID' if valid else 'INVALID'
 require(result.output==expected,'RESULT_MISMATCH');return result

def aggregate(workload,states):
 require(type(workload) is WorkloadV1,'WORKLOAD_TYPE');workload.__post_init__();require(type(states) is tuple,'STATES');by={}
 for s in states:
  require(type(s) is TaskStateV1,'STATE_TYPE');s.__post_init__();require(s.task_id in {t.task_id for t in workload.tasks},'UNKNOWN_TASK')
  if s.task_id in by:require(by[s.task_id]==s,'CONFLICT')
  by[s.task_id]=s
 require(set(by)=={t.task_id for t in workload.tasks},'MISSING_RESULT');ordered=tuple(by[t.task_id] for t in workload.tasks)
 for task,s in zip(workload.tasks,ordered):
  require(s.status not in ('RUNNING','PENDING'),'UNFINISHED')
  if s.status=='SUCCEEDED':r=verify(task,WorkerResultV1(task.commitment,s.attempt,s.output));require(r.commitment==s.result_commitment,'RESULT_COMMITMENT')
 status='STOPPED' if any(s.status=='CANCELLED' for s in ordered) else ('COMPLETE_ISOLATED' if all(s.status=='SUCCEEDED' for s in ordered) else 'PARTIAL_FAILURE')
 return ParallelOutcomeV1(workload.commitment,ordered,status)
