from research_test_helpers import *
class Contracts(unittest.TestCase):
 def test_canonical(self):d=domain('A');self.assertEqual(parse(ResearchDomainV1,canonical(d)),d)
 def test_verified(self):
  with self.assertRaises(ResearchError):replace(domain('A'),trust='VERIFIED')
 def test_unknown(self):
  o=asdict(domain('A'));o['shell']='id'
  with self.assertRaises(ResearchError):parse(ResearchDomainV1,canonical(o))
 def test_loop_bound(self):
  with self.assertRaises(ResearchError):replace(budget(),max_iterations=10000)
 def test_retry(self):
  with self.assertRaises(ResearchError):replace(budget(),retries=1)
