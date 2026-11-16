"""Closed interpreter. No callbacks, generated code, paths or external effects."""
from cognitive_research_contracts import *
import time
INITIAL={'A':((0,1),(1,3)),'B':((0,0),(1,1)),'C':((1,2),(1,3))}
LIMITS={'A':('finite synthetic rule family; no external truth',),'B':('unobserved common cause prevents identification',),'C':('inconsistent supplied measurements',)}
ENVIRONMENT_COMMITMENT=commit('FixedEnvironment',dict(initial=INITIAL,oracle_A=(1,3,5,7,9),version='fixture-v1'))
def domain(environment_id,namespace='n',session_id='session',timestamp=10):
 require(environment_id in INITIAL,'ENVIRONMENT')
 args=(namespace,session_id,timestamp,(ENVIRONMENT_COMMITMENT,),'OBSERVED_SYNTHETIC','TEST_ONLY')
 obs=tuple(ResearchObservationV1(*args,x,y,'INITIAL',environment_id) for x,y in INITIAL[environment_id])
 return ResearchDomainV1(*args,environment_id,obs,LIMITS[environment_id])
def validate_domain(d):
 require(type(d) is ResearchDomainV1,'DOMAIN_TYPE');d.__post_init__();require(d==domain(d.environment_id,d.namespace,d.session_id,d.timestamp),'UNPINNED_DOMAIN')
def validate_observations(d,observations):
 validate_domain(d);require(type(observations) is tuple and len(observations)<=10,'OBSERVATION_BOUND')
 for o in observations:
  require(type(o) is ResearchObservationV1,'OBSERVATION_TYPE');o.__post_init__();require((o.namespace,o.session_id,o.environment_id,o.timestamp,o.provenance)==(d.namespace,d.session_id,d.environment_id,d.timestamp,d.provenance),'OBSERVATION_BINDING')
  if o.origin=='INITIAL':require((o.x,o.y) in INITIAL[d.environment_id],'FABRICATED_EVIDENCE')
  else:require(d.environment_id=='A' and o.y==(1,3,5,7,9)[o.x],'FABRICATED_EVIDENCE')
def run_experiment(d,experiment,budget,used_experiments=0,used_steps=0):
 started=time.monotonic();validate_domain(d);require(type(experiment) is ResearchExperimentV1 and type(budget) is ResearchBudgetV1,'TYPE');experiment.__post_init__();budget.__post_init__();typed(used_experiments,int);typed(used_steps,int)
 require((experiment.namespace,experiment.session_id)==(d.namespace,d.session_id)==(budget.namespace,budget.session_id),'SCOPE');require(experiment.domain_commitment==d.commitment,'DOMAIN_BINDING');require(d.environment_id=='A','NOT_IDENTIFIABLE')
 require(used_experiments<budget.max_experiments and used_steps+experiment.steps<=budget.max_steps,'BUDGET_EXHAUSTED')
 require(experiment.experiment_id==commit('ExperimentID',dict(domain=d.commitment,question=experiment.question_commitment,x=experiment.x)),'EXPERIMENT_ID')
 o=ResearchObservationV1(d.namespace,d.session_id,d.timestamp,d.provenance,'OBSERVED_SYNTHETIC','TEST_ONLY',experiment.x,(1,3,5,7,9)[experiment.x],'EXPERIMENT','A')
 e=ResearchEvidenceV1(d.namespace,d.session_id,d.timestamp,d.provenance,'INFERRED','TEST_ONLY',experiment.commitment,o.commitment,ENVIRONMENT_COMMITMENT)
 require((time.monotonic()-started)*1000<=budget.timeout_ms,'DEADLINE');return o,e
