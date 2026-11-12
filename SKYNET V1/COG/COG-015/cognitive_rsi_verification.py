"""Separate decision evidence; recompute instead of trusting self-reported metrics."""
from cognitive_rsi_contracts import *
from cognitive_rsi_evaluation import evaluate,simulate
from cognitive_rsi_baseline import fixture
def challenge(b,c,claimed):
 actual=evaluate(b,c);require(type(claimed) is ImprovementEvaluationV1 and claimed==actual,'EVALUATION_TAMPER');held=simulate(b,c.proposal.strategy,True);_,labels=fixture(b.scenario,True)
 # Independently recount raw outcomes against fixed labels.
 count=sum(o==e for o,e in zip(held.outputs,labels));require(count==held.correct and held.expected==labels,'METRIC_TAMPER');status='REGRESSION' if actual.regressions or count<len(labels) else 'CONSISTENT'
 return ImprovementChallengeV1(b.namespace,b.session_id,(actual.commitment,),'TEST_ONLY',c.commitment,actual.commitment,count,len(labels),status)
