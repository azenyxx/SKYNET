from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_stop(self):self.assertEqual(decide(session().evaluation,'STOP').reason,'META_STOP')
 def test_budget(self):self.assertEqual(decide(session().evaluation,'CONTINUE',0).reason,'BUDGET')
 def test_override(self):
  with self.assertRaises(TransferError):decide(session().evaluation,'EXECUTE')
