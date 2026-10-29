from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_reopen(self):
  from cognitive_transfer_registry import TransferRegistry
  with tempfile.TemporaryDirectory() as d:
   p=str(Path(d)/'r');r=TransferRegistry(p,True);s=session();r.append(s,0);r.close();r=TransferRegistry(p);self.assertEqual(r.replay('n'),(s,));self.assertEqual(r.replay('other'),());r.close()
 def test_stale_duplicate(self):
  from cognitive_transfer_registry import TransferRegistry
  with tempfile.TemporaryDirectory() as d:
   r=TransferRegistry(str(Path(d)/'r'),True);s=session();r.append(s,0)
   for rev in (0,1):
    with self.assertRaises(TransferError):r.append(s,rev)
   self.assertEqual(len(r.verify()),1);r.close()
 def test_corruption(self):
  from cognitive_transfer_registry import TransferRegistry
  with tempfile.TemporaryDirectory() as d:
   r=TransferRegistry(str(Path(d)/'r'),True);r.append(session(),0);r.db.execute('DROP TRIGGER no_update');r.db.execute("UPDATE events SET commitment='bad'")
   with self.assertRaises(TransferError):r.verify()
   r.close()
