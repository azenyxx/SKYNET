from world_test_helpers import *
class StoreTests(Fixture,unittest.TestCase):
 def test_reopen_history(self):
  a=self.add(observation());b=self.add(observation(kind='ATTRIBUTE',value='1',oid='o2'));self.store.close();self.store=WorldStore(self.path);self.assertEqual(a,self.store.state('n',1));self.assertEqual(b,self.store.state('n'))
 def test_duplicate(self):
  o=observation();self.add(o)
  with self.assertRaises(WorldError):self.add(o)
 def test_corruption(self):
  self.add(observation());self.store.db.execute('DROP TRIGGER no_update');self.store.db.execute("UPDATE events SET state_commitment='bad'")
  with self.assertRaises(WorldError):self.store.state('n')
 def test_schema(self):
  self.store.db.execute('CREATE TABLE unwanted(x)')
  with self.assertRaises(WorldError):self.store.state('n')

class BenchmarkTests(unittest.TestCase):
 def test_100_entities(self):
  import time,json
  from cognitive_world_graph import traverse
  from cognitive_causal_engine import reason
  from cognitive_world_simulator import simulate
  with tempfile.TemporaryDirectory() as tmp:
   s=WorldStore(str(Path(tmp)/'b'),True);state=empty('n');es=[]
   for i in range(100):
    e=event(state,observation('e'+str(i),oid='o'+str(i)));state=apply_event(state,e);es.append(e)
   t=time.perf_counter();s.append_many(tuple(es));insert=time.perf_counter()-t;t=time.perf_counter();snapshot=s.state('n');reconstruct=time.perf_counter()-t
   self.assertEqual(len(snapshot.entities),100);q=WorldQueryV1('n',P,'UNKNOWN','UNVERIFIED','e0',8,64,20);t=time.perf_counter();traverse(snapshot,q);graph=time.perf_counter()-t
   t=time.perf_counter();reason(model(),snapshot.commitment);causal=time.perf_counter()-t;t=time.perf_counter();simulate(model(),snapshot,());simulation=time.perf_counter()-t;s.close()
  Path(__file__).with_name('BENCHMARK_RESULTS.json').write_text(json.dumps({'tiers':[{'entities':100,'status':'MEASURED','insertion_seconds':insert,'reconstruction_seconds':reconstruct,'graph_seconds':graph,'causal_seconds':causal,'simulation_seconds':simulation,'graph_edges':0,'causal_nodes':2,'peak_memory':'NOT_MEASURED'},{'entities':1000,'status':'NOT_TESTED','reason':'V1 state cap128'},{'entities':10000,'status':'NOT_TESTED','reason':'V1 state cap128'}]},indent=2))
