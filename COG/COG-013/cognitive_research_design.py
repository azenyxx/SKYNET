from cognitive_research_contracts import *
from cognitive_research_hypotheses import prediction
from cognitive_research_runner import validate_observations
def design(d,q,hypotheses,observations):
 validate_observations(d,observations);require(type(q) is ResearchQuestionV1 and q.namespace==d.namespace and q.session_id==d.session_id,'QUESTION_SCOPE');require(type(hypotheses) is tuple and 1<=len(hypotheses)<=8,'HYPOTHESIS_BOUND')
 survivors=[h for h in hypotheses if all(prediction(h,o.x)==o.y for o in observations)]
 require(len(survivors)>1,'NO_DISCRIMINATION_NEEDED');used={o.x for o in observations};choices=[]
 for x in range(5):
  if x not in used:choices.append((-len({prediction(h,x) for h in survivors}),x))
 require(bool(choices),'PARAMETERS_EXHAUSTED');_,x=min(choices);outputs=tuple(prediction(h,x) for h in survivors)
 return ResearchExperimentV1(d.namespace,d.session_id,d.timestamp,(q.commitment,),'HYPOTHESIZED','TEST_ONLY',commit('ExperimentID',dict(domain=d.commitment,question=q.commitment,x=x)),d.commitment,q.commitment,'QUERY_FIXED_ENVIRONMENT',x,outputs,1)
