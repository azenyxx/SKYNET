import unittest
from pathlib import Path
import io,zipfile,json
from dataclasses import replace
import test_rollback_safety_engine as fixture
from integrated_qualification_contracts import *
import rsi_qualification_engine as engine
class Tests(unittest.TestCase):
 def setUp(self):
  f=fixture.Tests();f.setUp();self.f=f;self.call=(f.source,f.target,f.transition,f.dependency,f.plan,f.restoration,f.call,f.result,f.policy,f.state);self.result=f.go();self.policy=engine.policy();self.state=engine.initial()
  self.blobs=tuple((k,Path(v).read_bytes()) for k,v in {'RSI-001': '/workspace/scratch/5effddbda3d2/RSI-001/SKYNET-RSI-001-RELEASE.zip', 'RSI-002': '/workspace/scratch/5effddbda3d2/RSI-002/SKYNET-RSI-002-RELEASE.zip', 'RSI-003': '/workspace/scratch/5effddbda3d2/RSI-003/SKYNET-RSI-003-RELEASE.zip', 'RSI-004': '/workspace/scratch/5effddbda3d2/RSI-004/SKYNET-RSI-004-RELEASE.zip', 'RSI-005': '/workspace/scratch/5effddbda3d2/RSI-005/SKYNET-RSI-005-RELEASE.zip', 'RSI-006': '/workspace/scratch/5effddbda3d2/RSI-006/SKYNET-RSI-006-RELEASE.zip', 'RSI-007': '/workspace/scratch/5effddbda3d2/RSI-007-R2/SKYNET-RSI-007-R2-RELEASE.zip'}.items())
  self.records=tuple(engine.verify_archive(k,b) for k,b in self.blobs)
 def go(self,**kw):
  controls=dict(state_pin=self.state.commitment,input_pin=digest((self.records,self.call,self.result,self.policy)),sequence=1);controls.update(kw);return engine.qualify(self.records,self.call,self.result,self.policy,self.state,artifact_blobs=self.blobs,**controls)
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
 def test13_findings(self):self.assertEqual(len(self.go()[1].unresolved_findings),52)
 def test14_rollback(self):self.assertEqual(self.result[1].simulation_status,'SIMULATION_PASSED')
 def test15_accounting(self):self.assertEqual(self.go()[0].cumulative_resource_usage,7)

 def remake(self,x,**kw):
  values={f.name:getattr(x,f.name) for f in fields(x) if f.name!='commitment'};values.update(kw);return make(type(x),**values)
 def test16_artifact_hash(self):
  k,b=self.blobs[0]
  with self.assertRaisesRegex(ValueError,'^ARTIFACT_HASH$'):engine.verify_archive(k,b+b'changed')
 def test17_manifest(self):
  k,b=self.blobs[0];buf=io.BytesIO()
  with zipfile.ZipFile(io.BytesIO(b)) as src,zipfile.ZipFile(buf,'w') as dst:
   for n in src.namelist():dst.writestr(n,b'{}' if n=='MANIFEST.json' else src.read(n))
  with self.assertRaisesRegex(ValueError,'^MANIFEST$'):engine.verify_archive(k,buf.getvalue())
 def test18_count(self):
  self.records=(self.remake(self.records[0],observed_test_results=(99,0,0,0)),)+self.records[1:]
  with self.assertRaisesRegex(ValueError,'^EVIDENCE_BINDING$'):self.go()
 def test19_synthetic_hash(self):
  self.records=(self.remake(self.records[0],artifact_commitment=digest('fake')),)+self.records[1:]
  with self.assertRaisesRegex(ValueError,'^EVIDENCE_BINDING$'):self.go()
 def test20_artifact_missing(self):
  self.blobs=()
  with self.assertRaisesRegex(ValueError,'^ARTIFACT_UNAVAILABLE$'):self.go()
 def test21_nested(self):
  with self.assertRaisesRegex(ValueError,'^MEMBER_TYPE$'):self.remake(self.records[0],evidence_refs=(None,))
 def test22_provenance(self):
  with self.assertRaisesRegex(ValueError,'^EVIDENCE_PROMOTION$'):make(QualificationEvidence,evidence_id='e',source_stage='RSI-001',source_artifact='a',evidence_type='LOCAL',provenance_class='INDEPENDENT',verification_status='VERIFIED',source_commitment='0'*64,limitations=())
 def test23_findings(self):
  with self.assertRaisesRegex(ValueError,'^FINDINGS$'):self.remake(self.go()[1],unresolved_findings=())
  self.assertEqual(len(engine.register()),52)
 def test24_exhaustive(self):
  with self.assertRaisesRegex(ValueError,'^POLICY$'):self.remake(self.policy,finding_rules='EXHAUSTIVE')
 def test25_authority(self):
  v=self.go()[1]
  with self.assertRaisesRegex(ValueError,'^AUTHORITY$'):self.remake(v,authorization_flags=((FLAGS[0],True),)+v.authorization_flags[1:])
 def test26_full(self):
  with self.assertRaisesRegex(ValueError,'^FALSE_FULL$'):self.remake(self.go()[1],series_status='SERIES_CLOSED_FULL_LIMITED_LOCAL_SCOPE')
 def test27_budget(self):
  self.policy=self.remake(self.policy,resource_limits=1)
  with self.assertRaisesRegex(ValueError,'^OPERATION_BUDGET$'):self.go()
 def test28_rollback_forgery(self):
  self.result=self.result[:1]+(self.result[0],)+self.result[2:]
  with self.assertRaisesRegex(ValueError,'^RESULT_BINDING$'):self.go()
 def test29_blocked_governance(self):
  self.assertEqual(self.result[2].governance_status,'NO_ELIGIBLE_CANDIDATE');self.assertEqual(dict(self.result[2].safety_gate_results)['GOVERNANCE_ELIGIBILITY'],'FAIL')
 def test30_regression_gate(self):
  self.assertIn('REGRESSION_STATUS',dict(self.result[2].safety_gate_results));self.assertEqual(self.go()[1].capability_results[-1],('autonomous_rsi','BLOCKED'))

if __name__=='__main__':unittest.main()
