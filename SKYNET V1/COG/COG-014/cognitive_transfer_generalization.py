from cognitive_transfer_contracts import *
from cognitive_transfer_hypotheses import hypothesize

def predict(source,target,h,task):
 require(h==hypothesize(source,target,h.mapping),'HYPOTHESIS_BINDING');require(type(task) is TransferTaskV1,'TASK_TYPE');task.__post_init__();require(task.namespace==target.namespace and task.target_commitment==target.commitment,'TASK_BINDING');out=();abstain=False
 if h.strategy=='TOPOLOGICAL':
  remaining={e.entity_id for e in target.entities};order=[]
  for _ in range(len(remaining)):
   ready=sorted(x for x in remaining if not any(r.target==x and r.source in remaining for r in target.relations))
   if not ready:abstain=True;break
   order.append(ready[0]);remaining.remove(ready[0])
  out=() if abstain else tuple(order)
 elif h.strategy=='CONSERVE':
  require(len(task.values)==3,'FLOW_INPUT');supply,demand,capacity=task.values;abstain=demand>supply or demand>capacity;out=() if abstain else (str(demand),str(supply-demand))
 elif h.strategy=='INTERVENTION_ONLY':abstain=True # no identified intervention contract available
 elif h.strategy=='GUARDED':
  require(len(task.values)==2,'STATE_INPUT');ids=tuple(sorted(e.entity_id for e in target.entities));a,b=task.values;require(a<len(ids) and b<len(ids),'STATE_INDEX');abstain=not task.authorized or not any(r.source==ids[a] and r.target==ids[b] for r in target.relations);out=() if abstain else ('VALID_SYNTHETIC_TRANSITION',)
 return TransferPredictionV1(target.namespace,(h.commitment,task.commitment),'TEST_ONLY',task.commitment,out,abstain,'HYPOTHESIZED')
def evaluate(source,target,h,tasks,labels):
 require(type(tasks) is tuple and 1<=len(tasks)<=32 and type(labels) is tuple and len(tasks)==len(labels),'EVAL_BOUND');require(len({t.task_id for t in tasks})==len(tasks),'DUPLICATE_TASK');evidence=[]
 for task,label in zip(tasks,labels):
  require(type(label) is tuple and all(type(x) is str for x in label),'LABEL');pred=predict(source,target,h,task);baseline=();evidence.append(TransferEvidenceV1(target.namespace,(task.commitment,pred.commitment),'TEST_ONLY',task,pred,label,baseline))
 answered=sum(not e.prediction.abstained for e in evidence);correct=sum(not e.prediction.abstained and e.prediction.output==e.expected for e in evidence);base=sum(e.baseline==e.expected for e in evidence);negative=sum(not e.prediction.abstained and e.prediction.output!=e.expected and e.baseline==e.expected for e in evidence)
 return TransferEvaluationV1(target.namespace,(source.commitment,target.commitment,h.commitment),'TEST_ONLY',tuple(evidence),len(evidence),answered,correct,base,negative,answered)
