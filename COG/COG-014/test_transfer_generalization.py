from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_four_pairs(self):
  for k in ('DAG','FLOW','CAUSAL','STATE'):
   s=session(k);self.assertEqual(s.evaluation.correct,0 if k=='CAUSAL' else 2)
 def test_negative(self):
  a,b=pair();h=hypothesize(a,b,discover(a,b).mapping);e=evaluate(a,b,h,cases(b),((),()));self.assertEqual(e.negative,2);self.assertEqual(decide(e,'CONTINUE').action,'ABSTAIN')
 def test_unauthorized(self):
  from cognitive_transfer_generalization import predict
  s=session('STATE');task=replace(cases(s.target)[0],authorized=False);self.assertTrue(predict(s.source,s.target,s.hypothesis,task).abstained)
 def test_infeasible(self):
  from cognitive_transfer_generalization import predict
  s=session('FLOW');task=replace(cases(s.target)[0],values=(1,4,2));self.assertTrue(predict(s.source,s.target,s.hypothesis,task).abstained)
 def test_no_labels_in_generation(self):
  import inspect
  self.assertEqual(tuple(inspect.signature(hypothesize).parameters),('source','target','m'))
