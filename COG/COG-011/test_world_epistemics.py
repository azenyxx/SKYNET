from world_test_helpers import *
from cognitive_world_epistemics import current_attributes,confidence_probability
class EpistemicTests(Fixture,unittest.TestCase):
 def test_late_observation(self):
  self.add(observation());self.add(observation(kind='ATTRIBUTE',value='new',event_time=5,oid='o2'));s=self.add(observation(kind='ATTRIBUTE',value='old',event_time=2,oid='o3'));self.assertEqual(current_attributes(s,20)[0][0].value,'new')
 def test_conflict(self):
  self.add(observation());self.add(observation(kind='ATTRIBUTE',value='x',oid='o2'));s=self.add(observation(kind='ATTRIBUTE',value='y',oid='o3'));a,c=current_attributes(s,20);self.assertEqual(a,());self.assertEqual(len(c),1)
 def test_revocation(self):
  self.add(observation());self.add(observation(kind='ATTRIBUTE',value='x',oid='o2'));s=self.add(observation(kind='REVOKE',value='eo2',oid='o3'));self.assertEqual(current_attributes(s,20)[0],())
 def test_calibration(self):
  with self.assertRaises(WorldError):confidence_probability(.99)
