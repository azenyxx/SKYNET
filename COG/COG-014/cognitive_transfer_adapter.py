from cognitive_transfer_contracts import *
from cognitive_transfer_analogy import discover
from cognitive_transfer_hypotheses import hypothesize
from cognitive_transfer_generalization import evaluate
from cognitive_transfer_strategy import decide
from cognitive_meta_runtime_adapter import observe_runtime
from cognitive_meta_audit import MetaAudit
from cognitive_research_registry import Registry as ResearchRegistry
from cognitive_transfer_registry import TransferRegistry

def transfer_cycle(source,target,tasks,labels,session_id,registry,expected_revision,meta_audit,research_registry,memory_store,memory_query,world_store,model,state,plan_request,plan_response,meta_budget,requested_memory_ids=()):
 require(type(registry) is TransferRegistry and type(meta_audit) is MetaAudit and type(research_registry) is ResearchRegistry,'CONTEXT_TYPE');require(source.namespace==target.namespace==memory_query.namespace==meta_budget.namespace,'NAMESPACE');require(session_id==meta_budget.trace_id,'SESSION_BINDING');prior=registry.replay(source.namespace);require(not any(s.session_id==session_id for s in prior),'SESSION_REPLAY')
 research=research_registry.replay(source.namespace);require(bool(research),'RESEARCH_DEPENDENCY');trace,meta,validation=observe_runtime(memory_store,memory_query,world_store,source.namespace,model,state,plan_request,plan_response,meta_budget,requested_memory_ids)
 require(not any(r.decision.action=='STOP' for r in meta_audit.replay(source.namespace)) and meta.action!='STOP','META_STOP');require(meta.action=='CONTINUE','META_RESTRICTED')
 candidate=discover(source,target);h=hypothesize(source,target,candidate.mapping);e=evaluate(source,target,h,tasks,labels);decision=decide(e,meta.action);s=TransferSessionV1(source.namespace,(trace.commitment,meta.commitment,research[-1].commitment),'TEST_ONLY',session_id,source,target,h,e,decision);return registry.append(s,expected_revision)
