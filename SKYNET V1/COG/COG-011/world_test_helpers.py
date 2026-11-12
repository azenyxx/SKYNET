import tempfile,unittest
from pathlib import Path
from dataclasses import replace,asdict
from cognitive_world_contracts import *
from cognitive_world_transitions import empty,apply_event
from cognitive_world_store import WorldStore
P=('0'*64,)
def observation(mid='a',kind='ENTITY',value='thing',target='',event_time=1,oid='o1',namespace='n',predicate='p'):
 args=(namespace,P,'OBSERVED','UNVERIFIED');e=WorldEvidenceRefV1(*args,'e'+oid,'0'*64,False);o=WorldObservationV1(*args,oid,kind,mid,predicate,value,target,event_time,max(10,event_time),100,e);return replace(o,evidence=replace(e,content_commitment=o.content_commitment))
def event(state,o,eid=None):return WorldEventV1(state.namespace,P,'OBSERVED','UNVERIFIED',eid or o.observation_id,state.revision,state.commitment,max(state.commit_time,o.observed_at),o)
def model():
 args=('n',P,'HYPOTHESIZED','UNVERIFIED');a=WorldHypothesisV1(*args,'x','CONST',(),0,('fixed disturbance',));b=WorldHypothesisV1(*args,'y','COPY',('x',),0,('structural assignment',));return CausalModelV1(*args,'model1',(a,b),('synthetic Boolean SCM only',),(),('unmeasured real-world causes',))
class Fixture:
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'world');self.store=WorldStore(self.path,True)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def add(self,o):return self.store.append(event(self.store.state(o.namespace),o))
