from cognitive_rsi_contracts import *
from cognitive_rsi_baseline import freeze
from cognitive_rsi_evaluation import observe,evaluate
from cognitive_rsi_proposals import propose
from cognitive_rsi_verification import challenge
from cognitive_rsi_policy import decide
from cognitive_rsi_registry import ImprovementRegistry,restore
from cognitive_meta_runtime_adapter import observe_runtime
from cognitive_meta_audit import MetaAudit
from cognitive_research_registry import Registry as ResearchRegistry
from cognitive_transfer_registry import TransferRegistry

def simulate_cycle(namespace,session_id,scenario,meta_action='CONTINUE',provenance=None):
 b=freeze(namespace,session_id,scenario);o=observe(b);c=propose(b,o);before=digest('Sandbox',dict(baseline=b.commitment,strategy=b.strategy));sandbox={'baseline':b.commitment,'strategy':b.strategy};saved=dict(sandbox)
 try:sandbox['strategy']=c.proposal.strategy;e=evaluate(b,c);ch=challenge(b,c,e);decision=decide(b,c,e,ch,meta_action)
 finally:sandbox.clear();sandbox.update(saved)
 require(digest('Sandbox',sandbox)==before,'RESTORE_FAILED');r=restore(b,before);return ImprovementSessionV1(namespace,session_id,provenance or (b.commitment,),'TEST_ONLY',b,o,c,e,ch,decision,r)

def improvement_cycle(namespace,session_id,scenario,registry,expected_revision,meta_audit,research_registry,transfer_registry,memory_store,memory_query,world_store,model,state,plan_request,plan_response,meta_budget,requested_memory_ids=()):
 require(type(registry) is ImprovementRegistry and type(meta_audit) is MetaAudit and type(research_registry) is ResearchRegistry and type(transfer_registry) is TransferRegistry,'CONTEXT_TYPE');require(namespace==memory_query.namespace==meta_budget.namespace and session_id==meta_budget.trace_id,'SCOPE');prior=registry.replay(namespace);require(not any(s.session_id==session_id for s in prior),'REPLAY');require(not any(s.decision.action=='STOP' for s in prior),'STOP_LATCH');research=research_registry.replay(namespace);transfers=transfer_registry.replay(namespace);require(bool(research) and bool(transfers),'DEPENDENCY')
 trace,meta,validation=observe_runtime(memory_store,memory_query,world_store,namespace,model,state,plan_request,plan_response,meta_budget,requested_memory_ids);require(not any(x.decision.action=='STOP' for x in meta_audit.replay(namespace)) and meta.action!='STOP','META_STOP');require(meta.action=='CONTINUE','META_RESTRICTED')
 s=simulate_cycle(namespace,session_id,scenario,meta.action,(trace.commitment,meta.commitment,research[-1].commitment,transfers[-1].commitment));return registry.append(s,expected_revision)
