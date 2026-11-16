from dataclasses import replace
import tempfile,unittest
from pathlib import Path
from cognitive_transfer_contracts import *
from cognitive_transfer_analogy import discover
from cognitive_transfer_hypotheses import hypothesize
from cognitive_transfer_generalization import evaluate
from cognitive_transfer_strategy import decide
H='0'*64
def pair(kind='DAG'):
 roles={'DAG':('NODE','NODE','NODE'),'FLOW':('SUPPLY','DEMAND','DEMAND'),'CAUSAL':('NODE','NODE','NODE'),'STATE':('STATE','STATE','STATE')}[kind]
 relation={'DAG':'PRECEDES','FLOW':'FLOWS','CAUSAL':'CAUSES','STATE':'TRANSITIONS'}[kind]
 constraints={'DAG':('DEPENDENCIES',),'FLOW':('CONSERVATION','CAPACITY'),'CAUSAL':('INTERVENTION_REQUIRED','CONFOUNDED'),'STATE':('AUTHORIZATION','GUARDS')}[kind]
 def domain(ids,name):return DomainSchemaV1('n',(H,),'TEST_ONLY',name,kind,tuple(DomainEntityV1(x,r) for x,r in zip(ids,roles)),(DomainRelationV1(ids[0],ids[1],relation),DomainRelationV1(ids[1],ids[2],relation)),tuple(DomainConstraintV1(x) for x in constraints),('finite_synthetic_structure_only',))
 return domain(('a','b','c'),'source'),domain(('x','y','z'),'target')
def cases(t):
 vals={'DAG':((1,), (2,)),'FLOW':((10,4,5),(7,3,4)),'CAUSAL':((0,),(1,)),'STATE':((0,1),(1,2))}[t.kind]
 return tuple(TransferTaskV1('n',(H,),'TEST_ONLY','held'+str(i),t.commitment,v,True,'HELD_OUT') for i,v in enumerate(vals))
def labels(kind):return {'DAG':(('x','y','z'),('x','y','z')),'FLOW':(('4','6'),('3','4')),'CAUSAL':((),()),'STATE':(('VALID_SYNTHETIC_TRANSITION',),('VALID_SYNTHETIC_TRANSITION',))}[kind]
def session(kind='DAG',sid='s'):
 a,b=pair(kind);h=hypothesize(a,b,discover(a,b).mapping);e=evaluate(a,b,h,cases(b),labels(kind));return TransferSessionV1('n',(H,),'TEST_ONLY',sid,a,b,h,e,decide(e,'CONTINUE'))
