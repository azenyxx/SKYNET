import unittest
from dataclasses import replace,FrozenInstanceError
import cognitive_unified as u

class Tests(unittest.TestCase):
 def setUp(self):
  e=u.ac.EvidenceReference('e','x',7,'observer',(),0,100,False)
  t=u.ac.VerificationTarget('target','producer','x',7,'DIRECT',('e',))
  r=u.ac.VerificationRequest('vr',t,('e',),'local-structural-v1',100,0,100,False)
  self.vi=u.VerificationInput(r,(e,),(('e',u.ac.commitment(e)),))
  c=u.bm.BenchmarkCase('case','EXACT','INCONCLUSIVE',0,'author','ref')
  self.bi=u.BenchmarkInput(u.bm.BenchmarkSuite('suite',(c,)),(),(u.bm.ObservationRecord('case','INCONCLUSIVE','observer','ref'),))
 def setup_run(self,combined=False):
  inputs=(('a',self.vi),('b',self.bi)) if combined else (('a',self.vi),)
  steps=(u.record(u.CognitiveStep,'a','request','verification',self.vi,100,evidence=('e',)),)
  if combined:steps+=(u.record(u.CognitiveStep,'b','request','benchmark',self.bi,100,('a',)),)
  signals=tuple((False,i) for i in range(len(steps)+1));deadline=100
  request=u.record(u.CognitiveRequest,'request','root','coordinator',inputs,1000)
  context=u.record(u.CognitiveContext,'context','request','coordinator',(signals,deadline),1000)
  return [request,context,steps,inputs,signals,deadline]
 def runone(self,combined=False):return u.coordinate(*self.setup_run(combined))
 def bad(self,fn):
  with self.assertRaises((u.IntegrationError,TypeError,ValueError)):fn()
 # Contracts five
 def test_schema(self):self.bad(lambda:replace(self.setup_run()[0],schema_version='v2'))
 def test_unknown_field(self):self.bad(lambda:replace(self.setup_run()[0],authority=True))
 def test_bool_budget(self):self.bad(lambda:replace(self.setup_run()[0],budget=True))
 def test_digest_format(self):self.bad(lambda:replace(self.setup_run()[0],input_commitment='bad'))
 def test_output_authority(self):self.bad(lambda:replace(self.runone(),production_authorized=True))
 # Registry five
 def test_registry_available(self):self.assertEqual(u.component_status('verification'),'AVAILABLE')
 def test_registry_unavailable(self):self.assertEqual(u.component_status('memory'),'UNAVAILABLE')
 def test_registry_unknown(self):self.bad(lambda:u.component_status('shell'))
 def test_adapter_binding(self):
  a=self.setup_run();a[2]=(replace(a[2][0],component='benchmark'),);self.bad(lambda:u.coordinate(*a))
 def test_input_binding(self):
  a=self.setup_run();a[2]=(replace(a[2][0],input_commitment='0'*64),);self.bad(lambda:u.coordinate(*a))
 # Dependencies five
 def test_order(self):
  a=self.setup_run(True);self.assertEqual(tuple(s.record_id for s in u.order(tuple(reversed(a[2])))),('a','b'))
 def test_cycle(self):
  a=self.setup_run(True);self.bad(lambda:u.order((replace(a[2][0],dependencies=('b',)),a[2][1])))
 def test_missing(self):self.bad(lambda:u.order((replace(self.setup_run()[2][0],dependencies=('absent',)),)))
 def test_duplicate(self):
  s=self.setup_run()[2][0];self.bad(lambda:u.order((s,s)))
 def test_self_cycle(self):self.bad(lambda:u.order((replace(self.setup_run()[2][0],dependencies=('a',)),)))
 # Lifecycle five
 def test_terminal(self):self.assertEqual(self.runone().verdict.status,'DIAGNOSTIC')
 def test_trace_stages(self):self.assertEqual(tuple(t.status for t in self.runone().trace),('REQUEST','VALIDATED','PLANNED','DISPATCHED','COLLECTED','VERIFICATION','AGGREGATED'))
 def test_result_count(self):self.assertEqual(len(self.runone(True).results),2)
 def test_error_preserved(self):
  old=self.vi;self.vi=replace(old,request=replace(old.request,policy_id='unknown'));self.assertEqual(self.runone().verdict.status,'BLOCKED')
 def test_benchmark_exception(self):
  self.bi=replace(self.bi,observations=(replace(self.bi.observations[0],outcome='wrong'),));self.assertEqual(self.runone(True).verdict.status,'ERROR')
 # Trust six
 def test_inconclusive(self):self.assertEqual(self.runone().results[0].verification,'INCONCLUSIVE')
 def test_no_promotion(self):self.assertFalse(self.runone().promotion_authorized)
 def test_no_production(self):self.assertFalse(self.runone().production_authorized)
 def test_no_override(self):self.bad(lambda:replace(self.setup_run()[2][0],verification='VERIFIED'))
 def test_evidence(self):self.assertEqual(self.runone().results[0].evidence_refs,('e',))
 def test_refuted_retained(self):
  self.vi=replace(self.vi,request=replace(self.vi.request,target=replace(self.vi.request.target,conclusion=8)));self.assertEqual(self.runone().results[0].verification,'REFUTED')
 # Boundaries five
 def signals(self,signals,deadline=100):
  a=self.setup_run(True);a[4]=signals;a[5]=deadline;a[1]=replace(a[1],input_commitment=u.digest((signals,deadline)));return u.coordinate(*a)
 def test_pre_stop(self):self.assertEqual(len(self.signals(((True,0),(False,1),(False,2))).results),0)
 def test_boundary_stop(self):self.assertEqual(len(self.signals(((False,0),(False,1),(True,2))).results),1)
 def test_deadline(self):self.assertEqual(self.signals(((False,0),(False,1),(False,2)),2).verdict.status,'DEADLINE')
 def test_budget(self):
  a=self.setup_run();a[0]=replace(a[0],budget=0);self.assertEqual(u.coordinate(*a).verdict.status,'BUDGET')
 def test_bad_clock(self):self.bad(lambda:self.signals(((False,2),(False,1),(False,3))))
 # Replay four
 def test_repeat(self):self.assertEqual(self.runone(),self.runone())
 def test_commitment(self):self.assertEqual(self.runone(True).commitment,self.runone(True).commitment)
 def test_input_immutable(self):
  before=u.digest(self.vi);self.runone();self.assertEqual(before,u.digest(self.vi))
 def test_trace_binding(self):self.assertEqual(self.runone().results[0].output_commitment,u.digest(self.runone().outputs[0]))
 # Real integration five
 def test_real_verifier(self):self.assertEqual(self.runone().outputs[0],u.av.verify(replace(self.vi.request,now=1),self.vi.evidence,self.vi.pins))
 def test_real_benchmark(self):self.assertIs(type(self.runone(True).outputs[1]),u.bm.BenchmarkRun)
 def test_combined_answer(self):self.assertEqual(self.runone(True).outputs[1].accuracy,1)
 def test_combined_independence(self):self.assertEqual(self.runone(True).outputs[1].independence,'NOT_ESTABLISHED')
 def test_standalone_measurement(self):
  p=u.bm.PredictionRecord('case','INCONCLUSIVE',0,'ANSWER','candidate','ref');bi=replace(self.bi,predictions=(p,))
  a=self.setup_run();a[3]=(('a',bi),);a[0]=replace(a[0],input_commitment=u.digest(a[3]));a[2]=(u.record(u.CognitiveStep,'a','request','benchmark',bi,100),)
  self.assertEqual(u.coordinate(*a).outputs[0].accuracy,1)

if __name__=='__main__':unittest.main()
