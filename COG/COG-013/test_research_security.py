from research_test_helpers import *
from cognitive_research_runner import validate_domain
class SecurityTests(Fixture,unittest.TestCase):
 def test_unpinned_domain(self):
  d=domain('A')
  with self.assertRaises(ResearchError):validate_domain(replace(d,observations=(replace(d.observations[0],y=2),)))
 def test_paths(self):
  with self.assertRaises(ResearchError):domain('A',session_id='../../etc')
 def test_immutable(self):
  import sqlite3
  self.run_cycle()
  with self.assertRaises(sqlite3.IntegrityError):self.r.db.execute('DELETE FROM sessions')
 def test_corruption(self):
  self.run_cycle();self.r.db.execute('DROP TRIGGER no_update');self.r.db.execute("UPDATE sessions SET commitment='bad'")
  with self.assertRaises(ResearchError):self.r.verify()
