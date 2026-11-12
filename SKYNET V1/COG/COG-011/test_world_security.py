from world_test_helpers import *
from cognitive_world_transitions import apply_event
from cognitive_world_simulator import predict
class SecurityTests(Fixture,unittest.TestCase):
 def test_prediction_not_event(self):
  with self.assertRaises(WorldError):self.store.append(predict(model(),empty('n')))
 def test_invalid_utf8(self):
  with self.assertRaises(WorldError):parse(WorldObservationV1,b'\xff')
 def test_duplicate_keys(self):
  with self.assertRaises(WorldError):parse(WorldObservationV1,b'{"x":1,"x":2}')
 def test_immutable(self):
  import sqlite3
  self.add(observation())
  with self.assertRaises(sqlite3.IntegrityError):self.store.db.execute('DELETE FROM events')

 def test_forged_nested_namespace(self):
  s=self.add(observation())
  with self.assertRaises(WorldError):replace(s,entities=(replace(s.entities[0],namespace='foreign'),))
 def test_simulation_never_writes(self):
  from cognitive_world_simulator import simulate
  s=self.add(observation());before=self.store.state('n');simulate(model(),s,());self.assertEqual(before,self.store.state('n'))
