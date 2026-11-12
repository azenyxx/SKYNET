import unittest,tempfile
from pathlib import Path
from dataclasses import replace,asdict
from cognitive_meta_contracts import *
from cognitive_meta_tracing import collect,STAGES,SOURCES
from cognitive_meta_audit import MetaAudit
H='0'*64
def trace(tid='trace',change=None):
 es=[]
 for i,k in enumerate(STAGES):
  outcome=change[1] if change and k==change[0] else ('HYPOTHETICAL' if k=='CAUSAL' else 'OK')
  es.append(MetaEventV1('n',tid,10,SOURCES[k],(H,),'OBSERVED','UNVERIFIED','e'+str(i),i,k,outcome,H,H,(i+1,0,0,0,0)))
 return collect('n',tid,10,tuple(es))
def budget(tid='trace'):return MetaBudgetV1('n',tid,10,'RUNTIME',(),'OBSERVED','UNVERIFIED',(100,10,10,1000,1000),0,1)
class Fixture:
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'audit');self.a=MetaAudit(self.path,True)
 def tearDown(self):self.a.close();self.tmp.cleanup()
