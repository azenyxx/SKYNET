from cognitive_research_contracts import *
from cognitive_research_runner import validate_observations
from cognitive_research_hypotheses import prediction

def evaluate(d,hypotheses,observations):
 validate_observations(d,observations);require(type(hypotheses) is tuple and 1<=len(hypotheses)<=8,'HYPOTHESES');groups={}
 for o in observations:groups.setdefault(o.x,set()).add(o.y)
 contradictory=any(len(v)>1 for v in groups.values());out=[]
 for h in hypotheses:
  require(type(h) is ResearchHypothesisV1 and (h.namespace,h.session_id)==(d.namespace,d.session_id),'HYPOTHESIS_SCOPE')
  if d.environment_id=='B':status='NOT_IDENTIFIABLE';matches=0
  elif contradictory:status='INCONCLUSIVE';matches=0
  else:
   matches=sum(prediction(h,o.x)==o.y for o in observations);status='SUPPORTED_WITHIN_MODEL' if matches==len(observations) else 'REFUTED_WITHIN_MODEL'
  out.append(ResearchResultV1(d.namespace,d.session_id,d.timestamp,(h.commitment,),'INFERRED','TEST_ONLY',h.commitment,status,matches,len(observations),tuple(o.commitment for o in observations)))
 return tuple(out)
