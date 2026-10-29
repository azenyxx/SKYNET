from test_memory_contracts import Fixture,record,unittest,replace,MemoryErrorV1,Path,MemoryStore,asdict,canonical
from cognitive_memory_contracts import *
class SecurityTests(Fixture,unittest.TestCase):
 def test_schema(self):
  self.s.db.execute('CREATE TABLE unexpected(x)')
  with self.assertRaises(MemoryErrorV1):self.s.verify()
 def test_head_tampering(self):
  self.active();self.s.db.execute("UPDATE heads SET revision=0")
  with self.assertRaises(MemoryErrorV1):self.s.verify()
 def test_history_commitment(self):
  self.active();self.s.db.execute('DROP TRIGGER immutable_update');self.s.db.execute("UPDATE revisions SET commitment='bad' WHERE revision=0");self.s.db.execute("CREATE TRIGGER immutable_update BEFORE UPDATE ON revisions BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END")
  with self.assertRaises(MemoryErrorV1):self.s.verify()
 def test_invalid_database(self):
  path=Path(self.tmp.name)/'bad';path.write_bytes(b'not a sqlite database')
  with self.assertRaises(Exception):MemoryStore(str(path))
