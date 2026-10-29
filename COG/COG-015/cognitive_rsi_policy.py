from cognitive_rsi_contracts import *
from cognitive_rsi_verification import challenge
def decide(b,c,e,ch,meta_action='CONTINUE'):
 require(meta_action in ('CONTINUE','STOP','ABSTAIN','REQUEST_EVIDENCE','RECONSIDER'),'META_ACTION');require(ch==challenge(b,c,e),'FAKE_CHALLENGE')
 if meta_action=='STOP':action,reason='STOP','META_STOP'
 elif ch.status!='CONSISTENT' or e.regressions or e.candidate_metrics.correct<e.baseline_metrics.correct:action,reason='REJECT','REGRESSION'
 elif meta_action!='CONTINUE':action,reason='ABSTAIN','NO_GAIN'
 elif e.candidate_metrics.correct>e.baseline_metrics.correct or e.candidate_metrics.operations<e.baseline_metrics.operations:action,reason='RECOMMEND_FOR_HUMAN_REVIEW','VERIFIED_SYNTHETIC_GAIN'
 else:action,reason='ABSTAIN','NO_GAIN'
 return ImprovementDecisionV1(b.namespace,b.session_id,(e.commitment,ch.commitment),'TEST_ONLY',c.commitment,action,reason)
