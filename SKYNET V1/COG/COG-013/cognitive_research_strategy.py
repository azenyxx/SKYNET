from cognitive_research_contracts import *
def select_next(d,results,budget,iterations,experiments,meta_action):
 require(meta_action in ('CONTINUE','STOP','ABSTAIN','REQUEST_EVIDENCE','RECONSIDER'),'META_ACTION');budget.__post_init__();typed(iterations,int);typed(experiments,int)
 if meta_action!='CONTINUE':action,why='STOP','META_STOP' if meta_action=='STOP' else 'META_RESTRICTION'
 elif d.environment_id=='B':action,why='REQUEST_EVIDENCE','CONFOUNDED'
 elif d.environment_id=='C':action,why='ABSTAIN','CONTRADICTORY'
 elif sum(r.status=='SUPPORTED_WITHIN_MODEL' for r in results)==1:action,why='STOP','CONFIRMED_WITHIN_MODEL'
 elif iterations>=budget.max_iterations or experiments>=budget.max_experiments or experiments>=budget.max_steps:action,why='STOP','BUDGET'
 else:action,why='RUN_ALLOWED_EXPERIMENT','COMPETING_RULES'
 return ResearchDecisionV1(d.namespace,d.session_id,d.timestamp,(d.commitment,),'INFERRED','TEST_ONLY',action,why)
