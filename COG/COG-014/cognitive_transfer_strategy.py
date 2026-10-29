from cognitive_transfer_contracts import *
def decide(e,meta_action,max_iterations=1):
 require(type(e) is TransferEvaluationV1,'EVAL_TYPE');typed(max_iterations,int);require(max_iterations<=4,'ITERATION_BOUND');require(meta_action in ('CONTINUE','STOP','ABSTAIN','REQUEST_EVIDENCE','RECONSIDER'),'META_ACTION')
 if meta_action=='STOP':action,reason='STOP','META_STOP'
 elif max_iterations==0:action,reason='STOP','BUDGET'
 elif meta_action!='CONTINUE' or not e.answered:action,reason='ABSTAIN','INSUFFICIENT_EVIDENCE'
 elif e.negative or e.correct<e.answered:action,reason='ABSTAIN','NEGATIVE_TRANSFER'
 else:action,reason='STOP','QUALIFIED_WITHIN_FIXTURE'
 return TransferDecisionV1(e.namespace,(e.commitment,),'TEST_ONLY',action,reason)
