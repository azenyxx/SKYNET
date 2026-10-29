from test_memory_contracts import Fixture,record,unittest,replace,MemoryErrorV1,Path,MemoryStore,asdict,canonical
from cognitive_memory_contracts import *
from cognitive_learning_controller import evaluate,promote,rollback
class LearningTests(unittest.TestCase):
 def proposal(self):
  h=commitment('Dataset',dict(ids=('a','b'),labels=('yes','no')));return LearningProposalV1('p',h,('train',),('a','b'),('no','no'),('yes','no'),('yes','no'))
 def test_improvement(self):p=self.proposal();e=evaluate(p,p.dataset_commitment);self.assertEqual((e.total,e.baseline_correct,e.candidate_correct),(2,1,2));self.assertEqual(e.status,'IMPROVEMENT_MEASURED')
 def test_regression(self):p=replace(self.proposal(),candidate=('yes','yes'));self.assertEqual(evaluate(p,p.dataset_commitment).status,'REGRESSION_REJECTED')
 def test_contamination(self):
  p=replace(self.proposal(),training_ids=('a',))
  with self.assertRaises(MemoryErrorV1):evaluate(p,p.dataset_commitment)
 def test_pinned_dataset(self):
  with self.assertRaises(MemoryErrorV1):evaluate(self.proposal(),'0'*64)
 def test_no_promotion(self):
  with self.assertRaises(MemoryErrorV1):promote(verified=True)
 def test_no_rollback_authority(self):
  with self.assertRaises(MemoryErrorV1):rollback(trusted=True)
