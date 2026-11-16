"""Evaluator-only exhaustive truth assignments, never an execution adapter."""
from itertools import product
from .contracts import validate,need

def truth(e,assignment):
 if type(e)is str:return assignment[e]
 op=e[0];a=truth(e[1],assignment)
 if op=='not':return not a
 b=truth(e[2],assignment)
 if op=='and':return a and b
 if op=='or':return a or b
 if op=='implies':return (not a) or b
 if op=='iff':return a==b
 raise ValueError('EXPRESSION')
def reference(t):
 vs=validate(t);models=[]
 for bits in product((False,True),repeat=len(vs)):
  a=dict(zip(vs,bits))
  if all(truth(e,a) for e in t['premises']):models.append(a)
 vals=[truth(t['query'],a) for a in models]
 answer='CONTRADICTION' if not vals else ('ENTAILED' if all(vals) else ('REFUTED' if not any(vals) else 'INSUFFICIENT_INFORMATION'))
 return {'answer':answer,'satisfying_assignments':len(models),'true_query_models':sum(vals),'false_query_models':len(vals)-sum(vals)}
