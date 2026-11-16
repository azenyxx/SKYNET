import multiprocessing,time
from cognitive_parallel_contracts import *
from cognitive_parallel_adapter import bind_plan
from cognitive_parallel_worker import worker
from cognitive_parallel_registry import ParallelRegistry
from cognitive_parallel_verification import aggregate,verify
from cognitive_planner import initial_progress,ready_steps,apply_decision
from cognitive_plan_contracts import PlanDecisionV1

def run(plan,workload,registry,test_faults=(),stop_after_go=False):
 require(type(registry) is ParallelRegistry,'REGISTRY_TYPE');require(type(test_faults) is tuple and len(test_faults)<=16 and type(stop_after_go) is bool,'TEST_CONTROLS');faults=dict(test_faults);require(len(faults)==len(test_faults) and set(faults)<={t.task_id for t in workload.tasks} and all(v in ('NORMAL','DELAY','CRASH') for v in faults.values()),'TEST_FAULTS')
 rebuilt=bind_plan(plan,workload.namespace,workload.workload_id,tuple((t.task_id,t.operation,t.payload) for t in workload.tasks),workload.workers,workload.timeout_ms,workload.queue_capacity);require(rebuilt==workload,'PLAN_BINDING');ns,wid=workload.namespace,workload.workload_id
 s=registry.read(ns,wid);require(s.workload==workload and not s.stopped,'WORKLOAD_BINDING');progress=initial_progress(plan);stats={'processes':0,'go':0,'peak_active':0,'reaped':0,'cleanup_failures':0};ctx=multiprocessing.get_context('fork');started=time.monotonic()
 # Restart is conservative: ambiguous RUNNING tasks are never dispatched again.
 if any(x.status=='RUNNING' for x in s.states):s=registry.change(ns,wid,s.revision,'RECOVER');return aggregate(workload,s.states),stats
 if any(x.status!='PENDING' for x in s.states):raise ParallelError('RESUME_REQUIRES_REVIEW')
 for _ in range(len(workload.tasks)):
  s=registry.read(ns,wid)
  if s.stopped:break
  ready=ready_steps(plan,progress)
  if not ready:break
  selected=sorted((t for t in workload.tasks if t.task_id in ready and next(x for x in s.states if x.task_id==t.task_id).status=='PENDING'),key=lambda t:(-t.priority,t.task_id))[:workload.workers]
  active=[]
  try:
   for task in selected:
    s=registry.change(ns,wid,s.revision,'CLAIM',task.task_id)
    endpoints=[]
    try:
     parent_recv,child_send=ctx.Pipe(duplex=False);endpoints.extend((parent_recv,child_send))
     child_recv,parent_send=ctx.Pipe(duplex=False);endpoints.extend((child_recv,parent_send))
     unused=(parent_recv,parent_send)+tuple(c for _,_,r,t,_ in active for c in (r,t))
     proc=ctx.Process(target=worker,args=(child_recv,child_send,unused,task,faults.get(task.task_id,'NORMAL')))
     proc.start()
    except BaseException:
     for endpoint in endpoints:endpoint.close()
     raise
    child_recv.close();child_send.close()
    active.append((task,proc,parent_recv,parent_send,time.monotonic()+workload.timeout_ms/1000));stats['processes']+=1;stats['peak_active']=max(stats['peak_active'],len(active))
   dispatched=set()
   startup_status={}
   # Issue GO to the entire ready wave before waiting for any computation result.
   for task,proc,pipe,send_pipe,deadline in active:
    try:
     if not pipe.poll(max(0,deadline-time.monotonic())):startup_status[task.task_id]='TIMED_OUT';continue
     if pipe.recv_bytes(16)!=b'READY':startup_status[task.task_id]='FAILED';continue
     current=registry.read(ns,wid)
     if current.stopped:break
     require(next(x for x in current.states if x.task_id==task.task_id).status=='RUNNING','CLAIM_LOST')
     send_pipe.send_bytes(b'GO');dispatched.add(task.task_id);stats['go']+=1
     if stop_after_go:registry.change(ns,wid,current.revision,'STOP');break
    except (EOFError,OSError,ValueError):startup_status[task.task_id]='FAILED'
   for task,proc,pipe,send_pipe,deadline in active:
    if registry.read(ns,wid).stopped:break
    status=startup_status.get(task.task_id,'FAILED');result=None
    if task.task_id in dispatched:
     try:
      if pipe.poll(max(0,deadline-time.monotonic())):
       result=parse(WorkerResultV1,pipe.recv_bytes(8192));verify(task,result);status='SUCCEEDED' if time.monotonic()<=deadline else 'TIMED_OUT'
      else:status='TIMED_OUT'
     except (EOFError,OSError,ValueError):status='FAILED';result=None
    current=registry.read(ns,wid)
    if current.stopped:break
    s=registry.change(ns,wid,current.revision,'RESULT',task.task_id,result if status=='SUCCEEDED' else None,status)
    if progress.outcome=='ACTIVE':progress=apply_decision(plan,progress,PlanDecisionV1('cog-plan-decision-v1',plan.plan_id,progress.revision,task.task_id,'COMPLETE' if status=='SUCCEEDED' else 'FAIL'))
  finally:
   for task,proc,pipe,send_pipe,deadline in active:
    try:
     if proc.is_alive():proc.terminate()
     proc.join(.2)
     if proc.is_alive():proc.kill();proc.join(.2)
     if proc.is_alive():stats['cleanup_failures']+=1
     else:stats['reaped']+=1
    except (OSError,ValueError):stats['cleanup_failures']+=1
    finally:
     try:pipe.close()
     finally:send_pipe.close()
  s=registry.read(ns,wid)
  if s.stopped or progress.outcome!='ACTIVE':break
 s=registry.read(ns,wid)
 if not s.stopped and any(x.status in ('PENDING','RUNNING') for x in s.states):s=registry.change(ns,wid,s.revision,'RECOVER')
 stats['wall_seconds']=time.monotonic()-started;out=aggregate(workload,s.states)
 if s.stopped:
  from dataclasses import replace
  out=replace(out,status='STOPPED')
 return out,stats
