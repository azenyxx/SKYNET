from cognitive_research_contracts import *
from cognitive_research_runner import validate_domain,validate_observations
def detect_gaps(d,observations=None):
 validate_domain(d);obs=d.observations if observations is None else observations;validate_observations(d,obs);groups={}
 for o in obs:groups.setdefault(o.x,set()).add(o.y)
 category='CONTRADICTORY' if any(len(v)>1 for v in groups.values()) else ('CONFOUNDED' if d.environment_id=='B' else 'COMPETING_RULES')
 return (ResearchGapV1(d.namespace,d.session_id,d.timestamp,(d.commitment,),'INFERRED','TEST_ONLY',category,2 if category!='COMPETING_RULES' else 1,d.commitment),)
