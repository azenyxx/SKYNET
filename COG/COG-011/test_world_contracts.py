from world_test_helpers import *
class Contracts(unittest.TestCase):
 def test_roundtrip(self):o=observation();self.assertEqual(o,parse(WorldObservationV1,canonical(o)))
 def test_forged_authority(self):
  with self.assertRaises(WorldError):replace(observation(),trust='VERIFIED')
 def test_unknown(self):
  o=asdict(observation());o['permissions']=True
  with self.assertRaises(WorldError):parse(WorldObservationV1,canonical(o))
 def test_schema(self):
  with self.assertRaises(WorldError):replace(observation(),schema='v2')
 def test_time(self):
  with self.assertRaises(WorldError):replace(observation(),event_time=-1)
 def test_payload(self):
  with self.assertRaises(WorldError):observation(value='x'*1025)
