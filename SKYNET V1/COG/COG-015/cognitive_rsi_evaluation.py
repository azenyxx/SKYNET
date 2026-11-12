from cognitive_rsi_contracts import *
from cognitive_rsi_baseline import fixture,validate_baseline
from cognitive_rsi_candidate import validate_candidate
from cognitive_transfer_contracts import DomainSchemaV1,DomainEntityV1,DomainRelationV1,DomainConstraintV1
from cognitive_transfer_analogy import discover
from cognitive_research_runner import domain
from cognitive_research_gaps import detect_gaps
from cognitive_research_hypotheses import generate,prediction
from cognitive_research_design import design

def simulate(b,strategy,challenge=False):
 validate_baseline(b);require(strategy in ('REPEAT','NAME_ONLY','MEMO','FAST','DISCRIMINATE','STRICT'),'OPERATION');xs,expected=fixture(b.scenario,challenge);out=[];ops=0;cache={}
 for x in xs:
  if b.scenario in ('RESOURCE','ACCURACY'):
   if strategy=='FAST':v=x;ops+=1
   elif strategy=='MEMO':
    if x not in cache:cache[x]=x*x;ops+=1
    v=cache[x]
   else:v=x*x;ops+=2;require(v==x*x,'LOCAL_CHECK')
   out.append(str(v))
  elif b.scenario=='RESEARCH':
   d=domain('A',namespace=b.namespace,session_id=b.session_id);q,hs=generate(d,detect_gaps(d)[0]);e=design(d,q,hs,d.observations);ops+=1 if strategy=='DISCRIMINATE' else 2
   survivors=[h.rule for h in hs if all(prediction(h,o.x)==o.y for o in d.observations) and prediction(h,e.x)==2*e.x+1];out.append(survivors[0] if len(survivors)==1 else 'ABSTAIN')
  else:
   if strategy=='NAME_ONLY':out.append('ACCEPT');ops+=1;continue
   def make(name,extra):
    es=tuple(DomainEntityV1(i,'NODE') for i in ('a','b','c'));rs=(DomainRelationV1('a','b','PRECEDES'),DomainRelationV1('b','c','PRECEDES'))+( (DomainRelationV1('c','a','PRECEDES'),) if extra else ())
    return DomainSchemaV1(b.namespace,(b.commitment,),'TEST_ONLY',name,'DAG',es,rs,(DomainConstraintV1('DEPENDENCIES'),),('fixed_synthetic_model',))
   try:discover(make('source',False),make('target',bool(x)));out.append('ACCEPT')
   except MemoryErrorV1:out.append('ABSTAIN')
   ops+=6 # declared bounded logical units, not CPU measurements
 correct=sum(a==e for a,e in zip(out,expected));abstain=sum(a=='ABSTAIN' and e=='ABSTAIN' for a,e in zip(out,expected));return ImprovementMetricV1(tuple(out),expected,correct,correct,ops,len(out)-correct,abstain,len(out))
def observe(b):
 m=simulate(b,b.strategy);return ImprovementObservationV1(b.namespace,b.session_id,(b.commitment,),'TEST_ONLY',b.commitment,m,False,'OBSERVED_SYNTHETIC')
def evaluate(b,c):
 validate_candidate(b,c);base=simulate(b,b.strategy);candidate=simulate(b,c.proposal.strategy);require(base.operations+candidate.operations<=c.operation_limit,'BUDGET_EXHAUSTED');reg=sum(a==e and n!=e for a,n,e in zip(base.outputs,candidate.outputs,base.expected))
 return ImprovementEvaluationV1(b.namespace,b.session_id,(b.commitment,c.commitment),'TEST_ONLY',b.commitment,c.commitment,base,candidate,reg)
