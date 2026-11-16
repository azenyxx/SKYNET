from test_memory_contracts import Fixture,record,unittest,replace,MemoryErrorV1,Path,MemoryStore,asdict,canonical
from cognitive_memory_contracts import *
from cognitive_memory_admission import validate_admission
class AdmissionTests(unittest.TestCase):
 def test_verified_denied(self):
  with self.assertRaises(MemoryErrorV1):validate_admission(record(trust='VERIFIED'))
 def test_tampered(self):
  with self.assertRaises(MemoryErrorV1):validate_admission(replace(record(),value='changed'))
 def test_revoked(self):
  r=record()
  with self.assertRaises(MemoryErrorV1):validate_admission(replace(r,evidence=(replace(r.evidence[0],revoked=True),)))
 def test_untrusted_stays_untrusted(self):self.assertEqual(validate_admission(record(trust='UNVERIFIED')).trust,'UNVERIFIED')
