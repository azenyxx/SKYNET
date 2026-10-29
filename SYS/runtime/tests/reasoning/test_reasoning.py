import unittest,copy,ast,inspect
from unittest.mock import patch
from skynet_reasoning_validation.contracts import *
from skynet_reasoning_validation.benchmark import generate
from skynet_reasoning_validation.reference import truth,reference
from skynet_reasoning_validation.adapter import execute
from skynet_reasoning_validation.runner import run
from skynet_reasoning_validation.scoring import *
from skynet_validation.evidence import Invalid

def task(premises,query):
 return dict(schema='val002-v1',case_id='case',domain='R-002',partition='development',seed=1001,difficulty='basic',pair_id='pair',premises=premises,query=query)
class ReasoningTests(unittest.TestCase):
 def test_chain(self):self.assertEqual(reference(task(['p',['implies','p','q'],['implies','q','r']],'r'))['answer'],'ENTAILED')
 def test_modus_tollens(self):self.assertEqual(reference(task([['implies','p','q'],['not','q']],['not','p']))['answer'],'ENTAILED')
 def test_invalid_converse(self):self.assertEqual(reference(task([['implies','p','q'],'q'],'p'))['answer'],'INSUFFICIENT_INFORMATION')
 def test_refuted(self):self.assertEqual(reference(task([['not','p']],'p'))['answer'],'REFUTED')
 def test_unsatisfiable(self):self.assertEqual(reference(task(['p',['not','p']],'q'))['satisfying_assignments'],0)
 def test_indirect_contradiction(self):self.assertEqual(reference(task(['p',['implies','p','q'],['not','q']],'q'))['answer'],'CONTRADICTION')
 def test_constraint_exclusion(self):self.assertEqual(reference(task([['or','p','q'],['not',['and','p','q']],['not','q']],'p'))['answer'],'ENTAILED')
 def test_no_explosion_claim(self):self.assertEqual(reference(task(['p',['not','p']],'r'))['answer'],'CONTRADICTION')
 def test_empty_premises(self):self.assertEqual(reference(task([],'p'))['answer'],'INSUFFICIENT_INFORMATION')
 def test_tautology(self):self.assertEqual(reference(task([],['or','p',['not','p']]))['answer'],'ENTAILED')
 def test_schema(self):
  t=task([],'p');t['schema']='bad'
  with self.assertRaisesRegex(Invalid,'^SCHEMA$'):validate(t)
 def test_unknown_operator(self):
  with self.assertRaisesRegex(Invalid,'^EXPRESSION$'):validate(task([],['execute','p']))
 def test_arity(self):
  with self.assertRaisesRegex(Invalid,'^ARITY$'):validate(task([],['and','p']))
 def test_variable_bound(self):
  with self.assertRaisesRegex(Invalid,'^VARIABLE_BOUND$'):validate(task(['p'+str(i) for i in range(9)],'p0'))
 def test_depth(self):
  e='p'
  for i in range(10):e=['not',e]
  with self.assertRaisesRegex(Invalid,'^LOGIC_DEPTH$'):validate(task([],e))
 def test_boolean_seed(self):
  t=task([],'p');t['seed']=True
  with self.assertRaisesRegex(Invalid,'^SEED$'):validate(t)
 def test_premise_bound(self):
  with self.assertRaisesRegex(Invalid,'^PREMISES$'):validate(task(['p']*17,'p'))
 def test_answer_field_denied(self):
  t=task([],'p');t['expected']='ENTAILED'
  with self.assertRaisesRegex(Invalid,'^TASK_FIELDS$'):execute(t)
 def test_generation(self):self.assertEqual(generate('development'),generate('development'))
 def test_holdout_freeze(self):
  with self.assertRaisesRegex(Invalid,'^DIGEST$'):generate('holdout')
 def test_pair_reference_equivalence(self):
  cases=generate('validation')
  for a,b in zip(cases[::2],cases[1::2]):self.assertEqual(reference(a),reference(b))
 def test_partitions(self):self.assertFalse({t['case_id'] for t in generate('development')}&{t['case_id'] for t in generate('validation')})
 def test_coverage(self):self.assertEqual(len(generate('development')),48)
 def test_unavailable(self):self.assertEqual(execute(task(['p'],'p'))['status'],'UNAVAILABLE')
 def test_no_symbolic_track(self):self.assertEqual(execute(task(['p'],'p'),'added_symbolic')['status'],'NOT_TESTABLE')
 def test_invalid_track(self):
  with self.assertRaisesRegex(Invalid,'^TRACK$'):execute(task([],'p'),'merged')
 def test_adapter_oracle_isolation(self):
  with patch('skynet_reasoning_validation.reference.reference',side_effect=AssertionError('LEAK')):self.assertEqual(execute(task([],'p'))['status'],'UNAVAILABLE')
 def test_no_reference_import(self):
  import skynet_reasoning_validation.adapter as a
  self.assertNotIn('reference',[x.module for x in ast.walk(ast.parse(inspect.getsource(a))) if isinstance(x,ast.ImportFrom)])
 def test_no_false_pass(self):self.assertEqual(score(execute(task([],'p')),{'answer':'ENTAILED'}),'UNAVAILABLE')
 def test_missing_provenance(self):
  with self.assertRaisesRegex(Invalid,'^MISSING_EXECUTION_EVIDENCE$'):score({'status':'EXECUTED','answer':'ENTAILED'},{'answer':'ENTAILED'})
 def test_metrics_missing(self):
  rows,_=run([task([],'p')]);m=metrics(rows);self.assertEqual(m['coverage']['value'],0);self.assertIsNone(m['accuracy_executed']['value']);self.assertIsNone(m['equivalent_consistency']['value'])
 def test_cross_track_rejection(self):
  a,_=run([task([],'p')]);t=task([],'q');t['case_id']='other';b,_=run([t],'added_symbolic')
  with self.assertRaisesRegex(Invalid,'^TRACK_MIXING$'):metrics(a+b)
 def test_evidence_tamper(self):
  rows,_=run([task([],'p')]);rows[0]['status']='PASS'
  with self.assertRaisesRegex(Invalid,'^EVIDENCE_DIGEST$'):validate_evidence(rows[0])
 def test_false_resealed_score(self):
  rows,_=run([task([],'p')]);e=rows[0];e.pop('evidence_digest');e['status']='PASS';e['evidence_digest']=commitment('val002-evidence',e)
  with self.assertRaisesRegex(Invalid,'^SCORE_BINDING$'):validate_evidence(e)
 def test_determinism(self):
  a,t=run(generate('development'));b,u=run(generate('development'));self.assertEqual(a,b);self.assertTrue(all(x>=0 for x in t.values()))
 def test_duplicates(self):
  with self.assertRaisesRegex(Invalid,'^DUPLICATE$'):run([task([],'p')]*2)
 def test_native_infrastructure_retained(self):
  from skynet_validation.adapter import execute as predecessor
  from skynet_validation.benchmark import generate as old
  t,e=next((t,e) for t,e in old('development') if t['domain']=='CAP-008');self.assertEqual(predecessor(t)['status'],'EXECUTED')
 def test_forged_native_execution(self):
  rows,_=run([task(['p'],'p')]);e=rows[0];e.pop('evidence_digest');e['output']={'status':'EXECUTED','answer':'ENTAILED','execution_interface':'fake.solver','provenance_reference':'0'*64};e['output_digest']=commitment('val002-output',e['output']);e['status']='PASS';e['evidence_digest']=commitment('val002-evidence',e)
  with self.assertRaisesRegex(Invalid,'^UNSUPPORTED_NATIVE_EXECUTION$'):validate_evidence(e)
 def test_forged_added_execution(self):
  rows,_=run([task(['p'],'p')],'added_symbolic');e=rows[0];e.pop('evidence_digest');e['output']={'status':'EXECUTED','answer':'ENTAILED','execution_interface':'fake.solver','provenance_reference':'0'*64};e['output_digest']=commitment('val002-output',e['output']);e['status']='PASS';e['evidence_digest']=commitment('val002-evidence',e)
  with self.assertRaisesRegex(Invalid,'^ABSENT_TRACK_EXECUTION$'):validate_evidence(e)
 def test_case_identity_binding(self):
  rows,_=run([task([],'p')]);e=rows[0];e.pop('evidence_digest');e['case_id']='wrong';e['evidence_digest']=commitment('val002-evidence',e)
  with self.assertRaisesRegex(Invalid,'^RECORD_BINDING$'):validate_evidence(e)
 def test_domain_identity_binding(self):
  rows,_=run([task([],'p')]);e=rows[0];e.pop('evidence_digest');e['domain']='R-008';e['evidence_digest']=commitment('val002-evidence',e)
  with self.assertRaisesRegex(Invalid,'^RECORD_BINDING$'):validate_evidence(e)
# Truth-table rows are independent Boolean reference fixtures, not system scores.
for op,fn in [('and',lambda a,b:a and b),('or',lambda a,b:a or b),('implies',lambda a,b:not a or b),('iff',lambda a,b:a==b)]:
 for a in (False,True):
  for b in (False,True):
   def test(self,op=op,a=a,b=b,expected=fn(a,b)):self.assertEqual(truth([op,'p','q'],{'p':a,'q':b}),expected)
   setattr(ReasoningTests,'test_truth_'+op+'_'+str(a)+'_'+str(b),test)
for a in (False,True):
 def test(self,a=a):self.assertEqual(truth(['not','p'],{'p':a}),not a)
 setattr(ReasoningTests,'test_negation_'+str(a),test)
if __name__=='__main__':unittest.main()
