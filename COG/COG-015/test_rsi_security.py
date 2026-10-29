from rsi_test_helpers import *
class Tests(unittest.TestCase):
 def test_no_metric_selection(self):
  import json
  for field in ('weights','fixtures','network_enabled','authority'):
   obj=json.loads(canonical(session().candidate));obj[field]=True
   with self.assertRaises(RSIError):parse(ImprovementCandidateV1,canonical(obj))
 def test_rollback_mismatch(self):
  from cognitive_rsi_registry import restore
  with self.assertRaises(RSIError):restore(freeze('n','s','RESOURCE'),H)
 def test_corruption(self):
  with tempfile.TemporaryDirectory() as d:
   r=ImprovementRegistry(str(Path(d)/'r'),True);r.append(session(),0);r.db.execute('DROP TRIGGER no_update')
   with self.assertRaises(RSIError):r.verify()
   r.close()
