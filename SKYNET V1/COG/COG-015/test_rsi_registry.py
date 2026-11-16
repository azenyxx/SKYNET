from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_reopen(self):
  with tempfile.TemporaryDirectory() as d:
   p=str(Path(d)/'r');r=ImprovementRegistry(p,True);s=session();r.append(s,0);r.close();r=ImprovementRegistry(p);self.assertEqual(r.replay('n'),(s,));self.assertEqual(r.replay('other'),());r.close()
 def test_duplicate_stale(self):
  with tempfile.TemporaryDirectory() as d:
   r=ImprovementRegistry(str(Path(d)/'r'),True);r.append(session(),0)
   for rev in (0,1):
    with self.assertRaises(RSIError):r.append(session(),rev)
   self.assertEqual(len(r.verify()),1);r.close()
 def test_stop_latch(self):
  with tempfile.TemporaryDirectory() as d:
   p=str(Path(d)/'r');r=ImprovementRegistry(p,True);r.append(session(action='STOP'),0);r.close();r=ImprovementRegistry(p)
   with self.assertRaises(RSIError):r.append(session(sid='next'),1)
   r.close()
