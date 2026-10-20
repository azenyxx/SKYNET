import unittest
from cog_public import Task, run, digest


class PublicDemoTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(run(Task('t1', 'normalize', '  hello   world ')).value, 'hello world')

    def test_count_words(self):
        self.assertEqual(run(Task('t2', 'count_words', 'one two three')).value, '3')

    def test_reverse(self):
        self.assertEqual(run(Task('t3', 'reverse', 'abc')).value, 'cba')

    def test_deterministic(self):
        task = Task('t4', 'normalize', '  a  b ')
        self.assertEqual(run(task), run(task))

    def test_disallow_operation(self):
        with self.assertRaises(ValueError):
            Task('t5', 'shell', 'echo hello')

    def test_bound_input(self):
        with self.assertRaises(ValueError):
            Task('t6', 'normalize', 'a' * 4097)

    def test_digest(self):
        self.assertEqual(digest({'a': 1, 'b': 2}), digest({'b': 2, 'a': 1}))

    def test_no_verification_claim(self):
        self.assertEqual(run(Task('t7', 'normalize', 'hello')).note, 'DEMO_ONLY_NOT_VERIFIED')


if __name__ == '__main__':
    unittest.main()
