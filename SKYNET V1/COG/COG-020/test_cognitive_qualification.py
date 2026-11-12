import unittest
from dataclasses import replace,FrozenInstanceError
import cognitive_qualification as q

class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.report=q.qualify()
 def bad(self,fn):
  with self.assertRaises((ValueError,TypeError)):fn()
 # Contracts 5
 def test_version(self):self.bad(lambda:replace(self.report,schema_version='v2'))
 def test_duplicates(self):self.bad(lambda:replace(self.report,evidence=self.report.evidence*2))
 def test_bad_digest(self):self.bad(lambda:replace(self.report,evidence_commitment='0'*64))
 def test_output_authority(self):self.bad(lambda:replace(self.report,production_authorized=True))
 def test_unknown_field(self):self.bad(lambda:replace(self.report,permission=True))
 # Architecture 5
 def test_registry(self):self.assertEqual(len({k for k,v in q.u.REGISTRY}),9)
 def test_missing_component(self):
  a=q.fixture();a[2]=(replace(a[2][0],component='memory'),a[2][1]);self.bad(lambda:q.u.coordinate(*a))
 def test_unknown_component(self):self.bad(lambda:q.u.component_status('shell'))
 def test_dependency_order(self):self.assertEqual(tuple(s.record_id for s in q.u.order(tuple(reversed(q.fixture()[2])))),('a','b'))
 def test_cycle(self):
  a=q.fixture();self.bad(lambda:q.u.order((replace(a[2][0],dependencies=('b',)),a[2][1])))
 # Integration 6
 def test_verifier_real(self):
  p=q.fixture()[3][0][1];self.assertEqual(q.av.verify(p.request,p.evidence,p.pins).status,'INCONCLUSIVE')
 def test_benchmark_real(self):self.assertIs(type(q.measured()),q.bm.BenchmarkRun)
 def test_coordinator_real(self):self.assertEqual(q.u.coordinate(*q.fixture()).verdict.status,'DIAGNOSTIC')
 def test_combined(self):self.assertEqual(q.u.coordinate(*q.fixture()).outputs[1].accuracy,1)
 def test_real_refutation(self):
  p=q.fixture()[3][0][1];r=replace(p.request,target=replace(p.request.target,conclusion=8));self.assertEqual(q.av.verify(r,p.evidence,p.pins).status,'REFUTED')
 def test_integrated_rejection(self):
  a=q.fixture();b=replace(a[3][1][1],observations=(replace(a[3][1][1].observations[0],outcome='wrong'),));a[3]=(a[3][0],('b',b));a[0]=replace(a[0],input_commitment=q.u.digest(a[3]));a[2]=(a[2][0],replace(a[2][1],input_commitment=q.u.digest(b)));self.assertEqual(q.u.coordinate(*a).verdict.status,'ERROR')
 # Evidence 7
 def test_malformed_evidence(self):
  p=q.fixture()[3][0][1];self.assertEqual(q.av.verify(p.request,(),()).status,'BLOCKED')
 def test_commitment_rejection(self):
  a=q.fixture();a[2]=(replace(a[2][0],input_commitment='0'*64),a[2][1]);self.bad(lambda:q.u.coordinate(*a))
 def test_no_verified(self):self.assertEqual(q.u.coordinate(*q.fixture()).results[0].verification,'INCONCLUSIVE')
 def test_no_certification(self):self.assertEqual(q.measured().independence,'NOT_ESTABLISHED')
 def test_self_evidence(self):
  p=q.fixture()[3][0][1];e=replace(p.evidence[0],source='producer');self.assertEqual(q.av.verify(p.request,(e,),(('e',q.ac.commitment(e)),)).status,'BLOCKED')
 def test_output_binding(self):
  out=q.u.coordinate(*q.fixture());self.assertEqual(out.results[0].output_commitment,q.u.digest(out.outputs[0]))
 def test_reference_defect_recorded(self):self.assertIn('C20-001',{f.record_id for f in self.report.findings})
 # Safety 5
 def test_stop(self):self.assertEqual(q.run_signals(((True,0),(False,1),(False,2))).verdict.status,'STOPPED')
 def test_partial_stop(self):self.assertEqual(len(q.run_signals(((False,0),(False,1),(True,2))).results),1)
 def test_deadline(self):self.assertEqual(q.run_signals(((False,0),(False,1),(False,2)),2).verdict.status,'DEADLINE')
 def test_budget(self):
  a=q.fixture();a[0]=replace(a[0],budget=0);out=q.u.coordinate(*a);self.assertEqual(out.verdict.status,'BUDGET');self.assertEqual(len(out.results),0)
 def test_no_privilege(self):self.assertFalse(q.u.coordinate(*q.fixture()).promotion_authorized)
 # Determinism 4
 def test_replay(self):self.assertEqual(self.report,q.qualify())
 def test_stable_commitment(self):self.assertEqual(self.report.commitment,q.qualify().commitment)
 def test_immutable(self):
  with self.assertRaises(FrozenInstanceError):self.report.verdict='PASS'
 def test_canonical(self):self.assertEqual(q.canonical(self.report),q.canonical(q.qualify()))
 # Measurement 4
 def test_known_calibration(self):
  m=q.measured();self.assertEqual(m.calibration.brier,q.F(1,25));self.assertEqual(m.calibration.ece,q.F(1,5))
 def test_numeric(self):
  c=q.bm.BenchmarkCase('c','NUMERIC',10,2,'author','ref');p=q.bm.PredictionRecord('c',12,1,'ANSWER','candidate','ref');o=q.bm.ObservationRecord('c',10,'observer','ref');self.assertEqual(q.bm.evaluate(q.bm.BenchmarkSuite('s',(c,)),(p,),(o,)).accuracy,1)
 def test_abstention(self):
  m=q.measured(None,0,'ABSTAIN');self.assertEqual(m.coverage,0);self.assertIsNone(m.selective_accuracy)
 def test_regression_incomparable(self):
  a=q.measured();b=replace(a,suite=replace(a.suite,suite_id='other'));self.assertEqual(q.bm.compare(a,b).status,'INCOMPARABLE')
 # Release and debt 4
 def test_no_rc(self):self.assertEqual(self.report.decision.eligibility,'LOCAL_RC_NOT_ELIGIBLE')
 def test_gate_promotion_rejects(self):self.bad(lambda:replace(self.report.decision,system_verdict='FULL',eligibility='LOCAL_RC_ELIGIBLE'))
 def test_debt_preserved(self):self.assertTrue({x[0] for x in q.DEBT}<={f.record_id for f in self.report.findings})
 def test_domains_complete(self):self.assertEqual({d.record_id for d in self.report.domains},{'Q1','Q2','Q3','Q4','Q5','Q6'})

if __name__=='__main__':unittest.main()
