import hashlib,json,re
from cognitive_parallel_contracts import *
from cognitive_plan_contracts import PlanStepV1,validate_graph
from cognitive_contracts import ResourcesV1

def _pairs(items):
 d={}
 for k,v in items:require(k not in d,'DUPLICATE_KEY');d[k]=v
 return d
def inputs(task):
 require(type(task) is ParallelTaskV1,'TASK_TYPE');task.__post_init__()
 if task.operation=='SHA256_TEXT_V1':return task.payload.encode('utf-8')
 if task.operation=='SUM_SQUARES_V1':
  require(re.fullmatch(r'[0-9]+(?:,[0-9]+){0,63}',task.payload) is not None,'NUMBERS');xs=tuple(int(x) for x in task.payload.split(','));require(all(x<=10000 for x in xs),'NUMBER_BOUND');return xs
 try:o=json.loads(task.payload,object_pairs_hook=_pairs)
 except (ValueError,UnicodeError):raise ParallelError('JSON') from None
 require(type(o) is dict and set(o)=={'nodes','edges','order'},'ORDER_SCHEMA');ns,es,order=o['nodes'],o['edges'],o['order'];require(type(ns) is list and 1<=len(ns)<=16 and all(type(x) is str for x in ns) and len(set(ns))==len(ns),'NODES');require(type(es) is list and len(es)<=32 and all(type(e) is list and len(e)==2 and all(type(x) is str and x in ns for x in e) for e in es),'EDGES');require(type(order) is list and all(type(x) is str for x in order),'ORDER');return o

def execute(task):
 v=inputs(task)
 if task.operation=='SHA256_TEXT_V1':return hashlib.sha256(v).hexdigest()
 if task.operation=='SUM_SQUARES_V1':
  total=0
  for n in v:total+=n*n
  return str(total)
 try:
  steps=tuple(PlanStepV1('cog-plan-step-v1',n,'ANALYZE',tuple(a for a,b in v['edges'] if b==n),ResourcesV1(1,0,0,0,0),0,'PENDING',0) for n in v['nodes']);validate_graph(steps)
  pos={n:i for i,n in enumerate(v['order'])};valid=len(v['order'])==len(v['nodes']) and set(pos)==set(v['nodes']) and all(pos[a]<pos[b] for a,b in v['edges'])
 except ValueError:valid=False
 return 'VALID' if valid else 'INVALID'
