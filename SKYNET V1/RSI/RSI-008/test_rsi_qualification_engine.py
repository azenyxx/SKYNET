import unittest
from dataclasses import replace
import test_rollback_safety_engine as fixture
from integrated_qualification_contracts import *
import rsi_qualification_engine as engine
class Tests(unittest.TestCase):
 def setUp(self):
  f=fixture.Tests();f.setUp();self.f=f;self.call=(f.source,f.target,f.transition,f.dependency,f.plan,f.restoration,f.call,f.result,f.policy,f.state);self.result=f.go();self.policy=engine.policy();self.state=engine.initial()
  self.records=tuple(make(StageQualificationRecord,stage_id=s,stage_version='v1',artifact_commitment=digest(s),reported_status='CLOSED_PARTIAL',observed_test_results=(0,0,0,0),integration_class='FIXTURE_BASED_ONLY',evidence_refs=('fixture',),qualification_limitations=('NO_ARTIFACT_AUTHENTICATION',)) for s in STAGES)
 def go(self,**kw):
  controls=dict(state_pin=self.state.commitment,input_pin=digest((self.records,self.call,self.result,self.policy)),sequence=1);controls.update(kw);return engine.qualify(self.records,self.call,self.result,self.policy,self.state,**controls)
 def test01_commitment(self):
  with self.assertRaisesRegex(ValueError,'^COMMITMENT$'):replace(self.records[0],commitment='0'*64)
 def test02_schema(self):
  with self.assertRaisesRegex(ValueError,'^VERSION$'):replace(self.records[0],schema_version='bad')
 def test03_missing(self):
  self.records=self.records[:-1]
  with self.assertRaisesRegex(ValueError,'^STAGES$'):self.go()
 def test04_duplicate(self):
  self.records=self.records[:-1]+(self.records[0],)
  with self.assertRaisesRegex(ValueError,'^DUPLICATE$'):self.go()
 def test05_stale(self):
  with self.assertRaisesRegex(ValueError,'^STATE_PIN$'):self.go(state_pin='0'*64)
 def test06_stop(self):
  with self.assertRaisesRegex(ValueError,'^STOPPED$'):self.go(stop=True)
 def test07_deadline(self):
  with self.assertRaisesRegex(ValueError,'^DEADLINE$'):self.go(now=1)
 def test08_pin(self):
  with self.assertRaisesRegex(ValueError,'^INPUT_PIN$'):self.go(input_pin='0'*64)
 def test09_replay(self):self.assertEqual(self.go(),self.go())
 def test10_chain(self):self.assertEqual(self.go()[1].integration_result,'FIXTURE_BASED_ONLY')
 def test11_flags(self):self.assertTrue(all(v is False for _,v in self.go()[1].authorization_flags))
 def test12_partial(self):self.assertEqual(self.go()[1].series_status,'SERIES_CLOSED_PARTIAL')
 def test13_findings(self):self.assertEqual(len(self.go()[1].unresolved_findings),49)
 def test14_rollback(self):self.assertEqual(self.result[1].simulation_status,'SIMULATION_PASSED')
 def test15_accounting(self):self.assertEqual(self.go()[0].cumulative_resource_usage,7)
if __name__=='__main__':unittest.main()
