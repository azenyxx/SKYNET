from research_test_helpers import *
class RegistryTests(Fixture,unittest.TestCase):
 def test_reopen(self):s=self.run_cycle();self.r.close();self.r=Registry(self.path);self.assertEqual(self.r.replay('n'),(s,))
 def test_duplicate(self):
  self.run_cycle()
  with self.assertRaises(ResearchError):self.run_cycle()
 def test_namespace(self):self.run_cycle();self.assertEqual(self.r.replay('other'),())
 def test_stale(self):
  s=self.run_cycle()
  with self.assertRaises(ResearchError):self.r.append(s,0)
 def test_tampered_result(self):
  s=self.run_cycle()
  with self.assertRaises(ResearchError):self.r.append(replace(s,results=(replace(s.results[0],matches=99),)+s.results[1:]),1)
