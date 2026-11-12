from research_test_helpers import *
from cognitive_research_gaps import detect_gaps
from cognitive_research_hypotheses import generate
from cognitive_research_design import design
class DesignTests(unittest.TestCase):
 def test_discriminator(self):d=domain('A');q,h=generate(d,detect_gaps(d)[0]);e=design(d,q,h,d.observations);self.assertEqual(e.x,2);self.assertEqual(set(e.expected_outputs),{5,7})
