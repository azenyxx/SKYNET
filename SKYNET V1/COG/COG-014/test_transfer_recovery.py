from transfer_test_helpers import *
class Tests(unittest.TestCase):
 def test_failed_write_no_partial(self):
  from cognitive_transfer_registry import TransferRegistry
  with tempfile.TemporaryDirectory() as d:
   p=str(Path(d)/'r');r=TransferRegistry(p,True)
   with self.assertRaises(TransferError):r.append(session(),2)
   r.close();r=TransferRegistry(p);self.assertEqual(r.verify(),());r.close()
