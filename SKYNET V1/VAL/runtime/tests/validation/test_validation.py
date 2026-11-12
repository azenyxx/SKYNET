import unittest,copy,inspect,json
from dataclasses import replace
from unittest.mock import patch
from skynet_validation.evidence import *
from skynet_validation.benchmark import generate,reference
from skynet_validation.adapter import execute
from skynet_validation.runner import run_case,run_cases
from skynet_validation.scoring import *
from skynet_validation.registry import registry

class ValidationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cases=generate('development');cls.records={d:run_case(*next((t,e) for t,e in cls.cases if t['domain']==d)) for d in ('CAP-001','CAP-002','CAP-003','CAP-004','CAP-005','CAP-007','CAP-008')}
 def task(self):return copy.deepcopy(self.cases[0][0])
 def bad(self,key,value,reason):
  t=self.task();t[key]=value
  with self.assertRaisesRegex(Invalid,'^'+reason+'$'):validate_task(t)
 def test01_schema(self):self.bad('schema','bad','SCHEMA')
 def test02_bool_seed(self):self.bad('seed',True,'SEED')
 def test03_identifier(self):self.bad('case_id','../escape','IDENTIFIER')
 def test04_domain(self):self.bad('domain','CAP-999','DOMAIN')
 def test05_difficulty(self):self.bad('difficulty','unbounded','DIFFICULTY')
 def test06_partition(self):self.bad('partition','secret','PARTITION')
 def test07_extra_answer(self):
  t=self.task();t['expected']='PASS'
  with self.assertRaisesRegex(Invalid,'^TASK_FIELDS$'):validate_task(t)
 def test08_float(self):
  with self.assertRaisesRegex(Invalid,'^TYPE$'):canonical(float('nan'))
 def test09_non_string_key(self):
  with self.assertRaisesRegex(Invalid,'^KEYS$'):canonical({1:'x'})
 def test10_nested_bound(self):
  x=[]
  for _ in range(14):x=[x]
  with self.assertRaisesRegex(Invalid,'^BOUND$'):canonical(x)
 def test11_size_bound(self):
  with self.assertRaisesRegex(Invalid,'^STRING$'):canonical('x'*16385)
 def test12_deterministic_canonical(self):self.assertEqual(canonical({'b':1,'a':2}),canonical({'a':2,'b':1}))
 def test13_domain_separation(self):self.assertNotEqual(commitment('one',{}),commitment('two',{}))
 def test14_generator_repeat(self):self.assertEqual(generate('validation'),generate('validation'))
 def test15_partitions_disjoint(self):
  a={t['case_id'] for t,e in generate('development')};b={t['case_id'] for t,e in generate('validation')};self.assertFalse(a&b)
 def test16_holdout_requires_freeze(self):
  with self.assertRaisesRegex(Invalid,'^DIGEST$'):generate('holdout')
 def test17_keys_separated(self):
  for t,e in self.cases:self.assertNotIn('expected',t);self.assertNotIn('answer',t['input'])
 def test18_adapter_no_oracle_import(self):
  import ast,skynet_validation.adapter as a
  tree=ast.parse(inspect.getsource(a));imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)];self.assertFalse(set(imports)&{'benchmark','scoring'})
 def test19_registry_ten(self):self.assertEqual(len(registry()),10);self.assertEqual(len({x['capability_id'] for x in registry()}),10)
 def test20_no_unexecuted_demonstration(self):self.assertNotIn('PARTIALLY_DEMONSTRATED',{x['qualification_status'] for x in registry()})
 def test21_unavailable_never_pass(self):self.assertEqual(self.records['CAP-003']['execution_status'],'UNAVAILABLE')
 def test22_forged_evidence(self):
  r=copy.deepcopy(self.records['CAP-001']);r['output']['answer']['verdict']='FAKE'
  with self.assertRaisesRegex(Invalid,'^EVIDENCE_COMMITMENT$'):validate_evidence(r)
 def test23_wrong_input_binding(self):
  r=copy.deepcopy(self.records['CAP-001']);r.pop('evidence_commitment');r['input_digest']='0'*64
  with self.assertRaisesRegex(Invalid,'^INPUT_BINDING$'):validate_evidence(seal(r))
 def test24_wrong_output_binding(self):
  r=copy.deepcopy(self.records['CAP-001']);r.pop('evidence_commitment');r['output_digest']='0'*64
  with self.assertRaisesRegex(Invalid,'^OUTPUT_BINDING$'):validate_evidence(seal(r))
 def test25_score_wrong_answer(self):
  r=self.records['CAP-001'];self.assertEqual(score(r['output'],{'verdict':'impossible'}),'FAIL')
 def test26_coverage_unavailable_denominator(self):
  m=metrics([self.records['CAP-001'],self.records['CAP-003']]);self.assertEqual(m['coverage']['value'],.5);self.assertEqual(m['accuracy_all']['value'],.5);self.assertEqual(m['accuracy_executed']['value'],1)
 def test27_no_transfer_claim(self):self.assertIsNone(metrics(list(self.records.values()))['transfer_gain']['value'])
 def test28_duplicate_records(self):
  with self.assertRaisesRegex(Invalid,'^DUPLICATE_CASE$'):metrics([self.records['CAP-001']]*2)
 def test29_case_bound(self):
  with self.assertRaisesRegex(Invalid,'^CASE_COUNT$'):run_cases([])
 def test30_deadline_bound(self):
  with self.assertRaisesRegex(Invalid,'^DEADLINE$'):run_cases(self.cases,max_seconds=0)
 def test31_timeout_bound(self):
  with self.assertRaisesRegex(Invalid,'^TIMEOUT$'):run_case(*self.cases[0],timeout=31)
 def test32_logical_api_execution(self):self.assertEqual(self.records['CAP-001']['execution_status'],'PASS');self.assertIn('skynet_sys_verification.Engine.evaluate',self.records['CAP-001']['system_interface'])
 def test33_fixed_pipeline(self):self.assertEqual(self.records['CAP-002']['execution_status'],'PASS');self.assertTrue(self.records['CAP-002']['output']['answer']['binding'])
 def test34_scheduling(self):self.assertEqual(self.records['CAP-004']['execution_status'],'PASS')
 def test35_memory_actual_value(self):self.assertEqual(self.records['CAP-005']['execution_status'],'PASS');self.assertEqual(self.records['CAP-005']['output']['answer']['provenance_status'],'UNVERIFIED')
 def test36_recovery_real(self):self.assertEqual(self.records['CAP-007']['execution_status'],'PASS');self.assertEqual(self.records['CAP-007']['output']['answer']['new_attempt'],2)
 def test37_uncertainty(self):
  t,e=next((t,e) for t,e in self.cases if t['domain']=='CAP-008' and not t['input']['votes']);r=run_case(t,e);self.assertEqual(r['execution_status'],'PASS');self.assertEqual(r['output']['answer']['verdict'],'INCONCLUSIVE')
 def test38_conflict(self):
  t,e=next((t,e) for t,e in self.cases if t['domain']=='CAP-001' and t['input']['votes']==['PASS','FAIL']);r=run_case(t,e);self.assertEqual(r['execution_status'],'PASS');self.assertTrue(r['output']['answer']['conflict'])
 def test39_failed_dependency(self):
  t,e=next((t,e) for t,e in self.cases if t['domain']=='CAP-004' and t['input']['fail_first']);r=run_case(t,e);self.assertEqual(r['execution_status'],'PASS');self.assertEqual(set(r['output']['answer']['states']),{'FAILED'})
 def test40_repeated_execution(self):
  t,e=self.cases[0];a=run_case(t,e);b=run_case(t,e);self.assertEqual(deterministic_digest([a]),deterministic_digest([b]));self.assertGreater(a['elapsed_ns'],0)
 def test41_no_shell_inputs(self):
  t=self.task();t['input']['shell']='echo injected'
  with self.assertRaisesRegex(Invalid,'^INPUT$'):execute(t)
 def test42_actual_failures_preserved(self):
  t=self.task();t['input']['policy']='all';t['input']['votes']=['FAIL']*3;r=run_case(t,reference(t));self.assertEqual(r['execution_status'],'PASS');self.assertEqual(r['output']['answer']['verdict'],'FAIL')
 def test43_serialization_roundtrip(self):
  for r in self.records.values():self.assertTrue(validate_evidence(json.loads(json.dumps(r))))
 def test44_unsupported_domains(self):
  for d in ('CAP-003','CAP-006','CAP-009','CAP-010'):
   t,e=next((t,e) for t,e in self.cases if t['domain']==d);self.assertEqual(execute(t)['status'],'UNAVAILABLE')
 def test45_false_pass_rejected(self):
  r=copy.deepcopy(self.records['CAP-003']);r.pop('evidence_commitment');r['execution_status']='PASS'
  with self.assertRaisesRegex(Invalid,'^NO_EXECUTION$'):validate_evidence(seal(r))
 def test46_observation_commitment(self):
  r=self.records['CAP-005'];o=r['output'];self.assertEqual(o['provenance_reference'],commitment('val001-observation-v1',{'calls':o['calls'],'details':o['details']}))
 def test47_partial_only(self):
  rows=registry(list(self.records.values()));self.assertNotIn('DEMONSTRATED',{x['qualification_status'] for x in rows});self.assertIn('PARTIALLY_DEMONSTRATED',{x['qualification_status'] for x in rows})
 def test48_adapter_failure_not_suppressed(self):
  t=self.task();t['input']['extra']='bad';r=run_case(t,None);self.assertEqual(r['execution_status'],'ERROR');self.assertIn('INPUT',r['output']['error'])
 def test49_no_negative_timing(self):
  r=copy.deepcopy(self.records['CAP-001']);r.pop('evidence_commitment');r['elapsed_ns']=-1
  with self.assertRaisesRegex(Invalid,'^TIMING$'):validate_evidence(seal(r))
 def test50_no_fake_execution(self):
  with self.assertRaisesRegex(Invalid,'^NO_EXECUTION$'):score({'status':'EXECUTED','answer':1,'calls':[],'provenance_reference':None},1)
 def test51_forged_provenance(self):
  r=copy.deepcopy(self.records['CAP-001']);r.pop('evidence_commitment');r['provenance_reference']='0'*64;r['output']['provenance_reference']='0'*64;r['output_digest']=commitment('val001-output-v1',r['output'])
  with self.assertRaisesRegex(Invalid,'^PROVENANCE_BINDING$'):validate_evidence(seal(r))
 def test52_actual_input_partition_isolation(self):
  a={commitment('input',t['input']) for t,e in generate('development')};b={commitment('input',t['input']) for t,e in generate('validation')};self.assertFalse(a&b)
 def test53_no_output_affects_generator(self):
  a=generate('development');r=copy.deepcopy(self.records['CAP-001']);r['output']['answer']='changed';self.assertEqual(a,generate('development'))
 def test54_paired_metrics(self):
  a=copy.deepcopy(self.records['CAP-001']);a.pop('evidence_commitment');a['task']['case_id']='paired';a['task']['input']['label']='new';a['input_digest']=commitment('val001-input-v1',a['task']);a=seal(a);m=paired_metrics([self.records['CAP-001'],a]);self.assertEqual(m['consistency']['value'],1);self.assertEqual(len(m['pairs']),1)
 def test55_reference_not_called_in_worker(self):
  with patch('skynet_validation.benchmark.reference',side_effect=AssertionError('ORACLE')):
   r=run_case(self.cases[0][0],self.cases[0][1]);self.assertEqual(r['execution_status'],'PASS')
 def test56_worker_read_and_effect_isolation(self):
  import subprocess,os,sys
  from pathlib import Path
  root=Path(__file__).resolve().parents[2]
  code="""import runpy,json
try:runpy.run_module('skynet_validation.worker',run_name='__main__')
except ValueError:pass
results=[]
for path,mode in [('audit/ANSWER-KEY.json','r'),('blocked-write','w')]:
 try:open(path,mode)
 except PermissionError as e:results.append(str(e))
try:__import__('skynet_validation.benchmark')
except PermissionError as e:results.append(str(e))
import socket
try:socket.socket()
except PermissionError as e:results.append(str(e))
print(json.dumps(results))
"""
  e=dict(os.environ,PYTHONPATH=str(root/'src'),PYTHONDONTWRITEBYTECODE='1');p=subprocess.run([sys.executable,'-c',code],input='{}',text=True,capture_output=True,env=e,cwd=root,timeout=10);self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),['VALIDATION_READ_DENIED','VALIDATION_WRITE_DENIED','ANSWER_KEY_DENIED','EXTERNAL_EFFECT_DENIED'])
if __name__=='__main__':unittest.main()
