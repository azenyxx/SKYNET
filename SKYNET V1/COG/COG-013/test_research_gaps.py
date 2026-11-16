from research_test_helpers import *
from cognitive_research_gaps import detect_gaps
class GapTests(unittest.TestCase):
 def test_A(self):self.assertEqual(detect_gaps(domain('A'))[0].category,'COMPETING_RULES')
 def test_B(self):self.assertEqual(detect_gaps(domain('B'))[0].category,'CONFOUNDED')
 def test_C(self):self.assertEqual(detect_gaps(domain('C'))[0].category,'CONTRADICTORY')
