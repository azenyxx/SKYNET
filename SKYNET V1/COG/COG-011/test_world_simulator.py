from world_test_helpers import *
from cognitive_world_simulator import simulate,predict
class SimulatorTests(unittest.TestCase):
 def test_do_replaces_assignment(self):
  s=empty('n');i=WorldInterventionV1('n',P,'HYPOTHESIZED','UNVERIFIED','x',1);r=simulate(model(),s,(i,));self.assertEqual(r.assignments,('x=1','y=1'));self.assertEqual(s,empty('n'));self.assertEqual(predict(model(),s).assignments,('x=0','y=0'))
 def test_determinism(self):self.assertEqual(simulate(model(),empty('n'),()),simulate(model(),empty('n'),()))
 def test_missing_equations(self):
  with self.assertRaises(WorldError):replace(model(),equations=())
 def test_version(self):
  with self.assertRaises(WorldError):replace(model(),model_version='')
