from meta_test_helpers import *
from cognitive_meta_monitor import monitor
class MonitorTests(unittest.TestCase):
 def test_labelled_detection(self):
  cases=[('MEMORY','REVOKED','EVIDENCE_REVOKED'),('WORLD','CONFLICT','CONTRADICTION'),('WORLD','STALE','STALE_CONTEXT'),('CAUSAL','NOT_IDENTIFIABLE','UNSUPPORTED_CAUSAL_CLAIM'),('PLAN_RESULT','REJECTED','VALIDATOR_REJECTION'),('CAUSAL','FACT_CLAIM','CONFIDENCE_MISREPRESENTATION'),('CAUSAL','CORRELATION_CAUSAL','UNSUPPORTED_CAUSAL_CLAIM'),('MEMORY','MISSING','MISSING_EVIDENCE')]
  for stage,outcome,code in cases:
   with self.subTest(code=code):self.assertIn(code,{f.code for f in monitor(trace(change=(stage,outcome)),budget())})
 def test_valid_no_findings(self):self.assertEqual(monitor(trace(),budget()),())
 def test_missing_evidence(self):
  t=trace();es=list(t.events);es[1]=replace(es[1],evidence=());self.assertIn('MISSING_EVIDENCE',{f.code for f in monitor(replace(t,events=tuple(es)),budget())})

class BenchmarkTests(unittest.TestCase):
 def test_fixture_benchmark(self):
  import time,json
  from cognitive_meta_tracing import validate_trace
  from cognitive_meta_policy import decide
  base=trace();es=[];kinds=['PLAN_START']+['RESOURCE']*94+list(STAGES[1:])
  start=time.perf_counter()
  for i,k in enumerate(kinds):es.append(MetaEventV1('n','bench',10,SOURCES[k],(H,),'OBSERVED','UNVERIFIED','e'+str(i),i,k,'HYPOTHETICAL' if k=='CAUSAL' else 'OK',H,H,(i+1,0,0,0,0)))
  try:
   t=collect('n','bench',10,tuple(es));append=time.perf_counter()-start;start=time.perf_counter();validate_trace(t);verification=time.perf_counter()-start;b=replace(budget('bench'),limits=(1000,10,10,1000,1000));start=time.perf_counter();decision=decide(t,b);monitor_latency=time.perf_counter()-start
   self.assertEqual(decision.action,'CONTINUE')
   with tempfile.TemporaryDirectory() as tmp:
    a=MetaAudit(str(Path(tmp)/'audit'),True)
    try:
     start=time.perf_counter();a.append(t,b,0);audit_append=time.perf_counter()-start;start=time.perf_counter();records=a.replay('n');audit_replay=time.perf_counter()-start;self.assertEqual(len(records),1)
    finally:a.close()
   result=dict(events=100,status='MEASURED',trace_collection_seconds=append,trace_verification_seconds=verification,decision_seconds=monitor_latency,audit_append_seconds=audit_append,audit_replay_seconds=audit_replay,peak_memory='NOT_MEASURED')
  except MetaContractError as e:result=dict(events=100,status='NOT_TESTED_FULL_TIER',reason=e.code)
  cases=[('MEMORY','REVOKED'),('WORLD','CONFLICT'),('WORLD','STALE'),('CAUSAL','NOT_IDENTIFIABLE'),('PLAN_RESULT','REJECTED'),('CAUSAL','FACT_CLAIM'),('CAUSAL','CORRELATION_CAUSAL'),('MEMORY','MISSING')]
  tp=sum(bool(monitor(trace(change=x),budget())) for x in cases);fp=int(bool(monitor(trace(),budget())));self.assertEqual((tp,fp),(8,0))
  Path(__file__).with_name('BENCHMARK_RESULTS.json').write_text(json.dumps(dict(tiers=[result,dict(events=1000,status='NOT_TESTED',reason='trace cap128'),dict(events=10000,status='NOT_TESTED',reason='trace cap128')],labelled_detection=dict(positives=8,negatives=1,true_positive=tp,false_negative=8-tp,false_positive=fp,true_negative=1-fp,scope='synthetic rule fixtures only')),indent=2))
