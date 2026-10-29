from meta_test_helpers import *
class SecurityTests(Fixture,unittest.TestCase):
 def test_no_decision_injection(self):
  with self.assertRaises(TypeError):self.a.append(trace(),budget(),0,decision='CONTINUE')
 def test_corrupt_commitment(self):
  self.a.append(trace(),budget(),0);self.a.db.execute('DROP TRIGGER immutable_update');self.a.db.execute("UPDATE records SET commitment='bad'");self.a.db.execute("CREATE TRIGGER immutable_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END")
  with self.assertRaises(MetaContractError):self.a.verify()
 def test_immutable(self):
  import sqlite3
  self.a.append(trace(),budget(),0)
  with self.assertRaises(sqlite3.IntegrityError):self.a.db.execute('DELETE FROM records')
 def test_stale(self):
  self.a.append(trace(),budget(),0)
  with self.assertRaises(MetaContractError):self.a.append(trace('next'),budget('next'),0)
