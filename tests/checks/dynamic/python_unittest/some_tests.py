import unittest

class FooTest(unittest.TestCase):
    def test_succeeds(self):
        pass

    def test_fails(self):
        self.assertTrue(False)
