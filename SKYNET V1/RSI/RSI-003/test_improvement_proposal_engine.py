import unittest
from dataclasses import replace
import test_bottleneck_discovery as fixture
import improvement_proposal_engine as engine
from improvement_hypothesis_contracts import *
class Tests(unittest.TestCase):
 def setUp(self):
  self.f=fixture.Tests();self.f.setUp();self.load();self.state=engine.initial()
 def load(self):
  f=self.f;self.args=(f.s,(f.m,),'PERFORMANCE',f.d,f.inputs,f.policy,f.state);self.result=f.go()
 def go(self,h='hyp-new',p='prop-new',baseline='',**kw):
  controls=dict(expected_state=self.state.state_commitment,approved_input=digest((self.args,self.result,h,p,'latency','LOWER',baseline)),sequence=self.state.sequence+1);controls.update(kw)
  return engine.construct(self.args,self.result,h,p,'latency','LOWER',baseline,self.state,**controls)
 def remake(self,x,**kw):
  v={f.name:getattr(x,f.name) for f in fields(x) if f.name!=seal(type(x))};v.update(kw);return make(type(x),**v)
 def test01_forged(self):
  with self.assertRaises(Exception):replace(self.go()[1][0],commitment='0'*64)
 def test02_version(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][0],schema_version='x')
 def test03_frozen(self):
  with self.assertRaises(Exception):self.go()[1][0].hypothesis_id='x'
 def test04_identity(self):
  with self.assertRaises(Exception):self.go(h='')
 def test05_bool_budget(self):
  with self.assertRaises(Exception):engine.initial(True)
 def test06_construct(self):self.assertEqual(self.go()[1][0].proposed_mechanism,'ALGORITHM_REFINEMENT')
 def test07_binding(self):self.assertEqual(self.go()[1][0].source_bottleneck_id,self.result[1].bottleneck_id)
 def test08_interfaces(self):self.assertEqual(self.go()[1][3].affected_interfaces,self.f.s.interface_commitments)
 def test09_mechanism(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][0],proposed_mechanism='EXECUTE')
 def test10_determinism(self):self.assertEqual(self.go(),self.go())
 def test11_baseline(self):self.assertEqual(self.go()[1][-1].decision,'BASELINE_REQUIRED')
 def test12_baseline_unverified(self):self.assertEqual(self.go(baseline='reported-baseline')[1][-1].decision,'INTEGRATION_NOT_QUALIFIED')
 def test13_unfalsifiable(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][2],falsification_conditions=())
 def test14_gain(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][2],predicted_magnitude=(20,))
 def test15_measurements(self):self.assertIn('OFFLINE_CONTROLLED_TEST',self.go()[1][2].measurement_requirements)
 def test16_independence(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][1][0],provenance_class='INDEPENDENTLY_VERIFIED')
 def test17_flags(self):
  v=self.go()[1][-1]
  with self.assertRaises(Exception):self.remake(v,authorization_flags=((FLAGS[0],True),)+v.authorization_flags[1:])
 def test18_findings(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][4],inherited_findings=())
 def test19_relaxation(self):
  with self.assertRaises(Exception):self.remake(self.go()[1][3],required_authorizations=())
 def test20_contradiction(self):
  f=self.f;ev=f.e;values={x.name:getattr(ev,x.name) for x in fields(ev) if x.name!='commitment'};values['provenance_class']='CONTRADICTED';ev=r.make(r.ImprovementEvidence,**values);ov={x.name:getattr(f.o,x.name) for x in fields(f.o) if x.name!='commitment'};ov['source_commitment']=r.digest((ev,));o=r.make(r.ImprovementObservation,**ov);f.inputs=(o,)+f.inputs[1:3]+((ev,),)+f.inputs[4:];self.load();self.assertEqual(self.go()[1][-1].decision,'CONTRADICTED')
 def test21_stop(self):
  with self.assertRaises(Exception):self.go(stop=True)
 def test22_deadline(self):
  with self.assertRaises(Exception):self.go(now=1,deadline=1)
 def test23_stale(self):
  with self.assertRaises(Exception):self.go(expected_state='0'*64)
 def test24_budget(self):
  self.state=engine.initial(1)
  with self.assertRaises(Exception):self.go()
 def test25_duplicates(self):
  self.state=self.go()[0]
  with self.assertRaises(Exception):self.go(p='different')
  with self.assertRaises(Exception):self.go(h='different')
 def test26_real_chain(self):self.assertEqual(self.go()[1][1][0].source_commitment,self.result[2][0].commitment)
 def test27_missing_source(self):
  self.result=()
  with self.assertRaises(Exception):self.go()
 def test28_forged_replay(self):
  self.result=(self.result[0],self.f.remake(self.result[1],bottleneck_id='forged'))+self.result[2:]
  with self.assertRaises(Exception):self.go()
 def test29_preserve_limits(self):self.assertEqual(self.go()[1][1][0].limitations,self.result[2][0].limitations)
 def test30_no_authority(self):self.assertTrue(all(v is False for k,v in self.go()[1][-1].authorization_flags))
if __name__=='__main__':unittest.main()
