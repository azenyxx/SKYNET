"""Public tests for typed validation and unsupported-error categories."""
import unittest
from skynet_v3.errors import SkyError, invalid, unsupported

class PublicErrorTests(unittest.TestCase):
    def test_invalid_category(self):
        err=invalid("BAD_FIELD", "$.field", "bad input")
        self.assertIsInstance(err, SkyError)
        self.assertEqual(err.to_dict(), {"category":"INVALID","code":"BAD_FIELD","path":"$.field","message":"bad input"})

    def test_unsupported_category(self):
        err=unsupported("UNKNOWN_KIND", "$.kind", "not supported")
        self.assertEqual(err.category, "UNSUPPORTED")
        self.assertIn("UNKNOWN_KIND", str(err))

if __name__ == "__main__": unittest.main()
