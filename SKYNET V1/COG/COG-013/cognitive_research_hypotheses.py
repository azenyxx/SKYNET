from cognitive_research_contracts import *
from cognitive_research_gaps import detect_gaps
def generate(d,gap):
 require(gap in detect_gaps(d),'UNGROUNDED_GAP');args=(d.namespace,d.session_id,d.timestamp,(gap.commitment,),'HYPOTHESIZED','TEST_ONLY')
 test={'COMPETING_RULES':'DISCRIMINATE_RULES','CONFOUNDED':'IDENTIFY_CAUSAL_EFFECT','CONTRADICTORY':'RESOLVE_CONFLICT'}[gap.category]
 q=ResearchQuestionV1(*args,commit('QuestionID',dict(domain=d.commitment,test=test)),gap.commitment,test)
 rules=('CAUSAL','COMMON_CAUSE') if gap.category=='CONFOUNDED' else ('LINEAR','QUADRATIC','CONSTANT')
 hs=tuple(ResearchHypothesisV1(*args,commit('HypothesisID',dict(question=q.commitment,rule=x)),x,('supplied finite model family only',),'INDEPENDENT_INTERVENTION_REQUIRED' if x in ('CAUSAL','COMMON_CAUSE') else 'ANY_MISMATCH') for x in rules)
 return q,hs
def prediction(h,x):
 require(type(h) is ResearchHypothesisV1,'HYPOTHESIS_TYPE');h.__post_init__();typed(x,int);require(x<=4,'PARAMETER_BOUND')
 if h.rule=='LINEAR':return 2*x+1
 if h.rule=='QUADRATIC':return x*x+x+1
 if h.rule=='CONSTANT':return 1
 raise ResearchError('NOT_IDENTIFIABLE')
