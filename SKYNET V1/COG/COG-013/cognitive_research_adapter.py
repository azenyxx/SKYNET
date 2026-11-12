from cognitive_research_contracts import *
from cognitive_research_runner import validate_domain,run_experiment
from cognitive_research_gaps import detect_gaps
from cognitive_research_hypotheses import generate
from cognitive_research_design import design
from cognitive_research_evaluation import evaluate
from cognitive_research_strategy import select_next
from cognitive_meta_runtime_adapter import observe_runtime
from cognitive_meta_audit import MetaAudit
from cognitive_research_registry import Registry

def research_cycle(d,budget,registry,expected_sequence,meta_audit,memory_store,memory_query,world_store,model,state,plan_request,plan_response,meta_budget,requested_memory_ids=()):
 validate_domain(d);require(type(budget) is ResearchBudgetV1 and type(registry) is Registry and type(meta_audit) is MetaAudit,'INPUT_TYPE');budget.__post_init__();require((budget.namespace,budget.session_id)==(d.namespace,d.session_id),'BUDGET_SCOPE')
 require(d.namespace==memory_query.namespace==meta_budget.namespace and d.session_id==meta_budget.trace_id,'CONTEXT_SCOPE')
 prior=registry.replay(d.namespace);require(not any(s.session_id==d.session_id for s in prior),'SESSION_REPLAY')
 gap=detect_gaps(d)[0];question,hypotheses=generate(d,gap);observations=d.observations;experiments=[];evidence=[];decisions=[];iterations=0
 for _ in range(budget.max_iterations+1):
  trace,meta,validation=observe_runtime(memory_store,memory_query,world_store,d.namespace,model,state,plan_request,plan_response,meta_budget,requested_memory_ids)
  latched=any(a.decision.action=='STOP' for a in meta_audit.replay(d.namespace));action='STOP' if latched else meta.action
  results=evaluate(d,hypotheses,observations);decision=select_next(d,results,budget,iterations,len(experiments),action);decisions.append(decision)
  if decision.action!='RUN_ALLOWED_EXPERIMENT':break
  x=design(d,question,hypotheses,observations);require(x.experiment_id not in {v.experiment_id for v in experiments},'EXPERIMENT_REPLAY');o,e=run_experiment(d,x,budget,len(experiments),len(experiments));experiments.append(x);evidence.append(e);observations+=(o,);iterations+=1
 else:raise ResearchError('ITERATION_BOUND')
 s=ResearchSessionV1(d.namespace,d.session_id,d.timestamp,(d.commitment,trace.commitment,meta.commitment),'INFERRED','TEST_ONLY',d,budget,question,hypotheses,tuple(experiments),observations,tuple(evidence),results,tuple(decisions),iterations,decision.action)
 registry.append(s,expected_sequence);return s
