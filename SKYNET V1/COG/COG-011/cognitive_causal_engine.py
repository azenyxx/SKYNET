from cognitive_world_contracts import *
def order(model):
 require(type(model) is CausalModelV1,'MODEL_TYPE');model.__post_init__();eq={x.variable:x for x in model.equations};require(len(eq)==len(model.equations),'DUPLICATE_VARIABLE')
 for x in eq.values():
  require(x.namespace==model.namespace and len(set(x.parents))==len(x.parents) and all(p in eq for p in x.parents),'PARENTS')
  require((x.operator=='CONST' and not x.parents) or (x.operator in ('COPY','NOT') and len(x.parents)==1) or (x.operator in ('AND','OR') and len(x.parents)==2),'EQUATION')
 result=[];remaining=set(eq)
 while remaining:
  ready=sorted(v for v in remaining if set(eq[v].parents)<=set(result));require(bool(ready),'CAUSAL_CYCLE');result.extend(ready);remaining.difference_update(ready)
 return tuple(eq[v] for v in result)
def reason(model,state_commitment,interventions=()):
 digest_text(state_commitment);equations=order(model);require(type(interventions) is tuple and len(interventions)<=32,'INTERVENTION_LIMIT');values={};do={}
 for i in interventions:
  require(type(i) is WorldInterventionV1,'INTERVENTION_TYPE');i.__post_init__();require(i.namespace==model.namespace and i.target in {e.variable for e in equations} and i.target not in do,'INTERVENTION_BINDING');do[i.target]=i.value
 assumptions=tuple(dict.fromkeys(model.assumptions+tuple(a for e in equations for a in e.assumptions)))
 if model.confounders or not model.assumptions or any(not e.assumptions for e in equations):return WorldReasoningResultV1(model.namespace,model.provenance,'UNKNOWN','UNVERIFIED',model.model_version,state_commitment,'NOT_IDENTIFIABLE',(),assumptions,model.alternatives)
 for e in equations:
  if e.variable in do:v=do[e.variable]
  elif e.operator=='CONST':v=e.constant
  elif e.operator=='COPY':v=values[e.parents[0]]
  elif e.operator=='NOT':v=1-values[e.parents[0]]
  elif e.operator=='AND':v=values[e.parents[0]] & values[e.parents[1]]
  else:v=values[e.parents[0]] | values[e.parents[1]]
  values[e.variable]=v
 return WorldReasoningResultV1(model.namespace,model.provenance,'HYPOTHESIZED','UNVERIFIED',model.model_version,state_commitment,'HYPOTHETICAL',tuple(k+'='+str(values[k]) for k in sorted(values)),assumptions,model.alternatives)
def causal_claim(edge):
 require(type(edge) is WorldCausalEdgeV1,'EDGE_TYPE');edge.__post_init__()
 return 'NOT_IDENTIFIABLE' if edge.claim!='HYPOTHESIZED_CAUSATION' or edge.confounders else 'HYPOTHESIS_ONLY'
