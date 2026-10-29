from world_test_helpers import *
class TransitionTests(Fixture,unittest.TestCase):
 def test_precondition(self):
  e=event(empty('n'),observation())
  with self.assertRaises(WorldError):self.store.append(replace(e,precondition_commitment='1'*64))
 def test_stale(self):
  e=event(empty('n'),observation());self.store.append(e)
  with self.assertRaises(WorldError):self.store.append(replace(e,event_id='new'))
 def test_hypothesis_denied(self):
  with self.assertRaises(WorldError):self.add(replace(observation(),epistemic='HYPOTHESIZED'))
 def test_tampered_evidence(self):
  with self.assertRaises(WorldError):self.add(replace(observation(),value='other'))
 def test_revoked_evidence(self):
  o=observation()
  with self.assertRaises(WorldError):self.add(replace(o,evidence=replace(o.evidence,revoked=True)))
