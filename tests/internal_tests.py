import unittest
import check50
import check50.internal

class TestRegisterAfterCheck(unittest.TestCase):
    def test_after_check(self):
        check50.internal.check_running = True
        l = []
        check50.internal.register.after_check(lambda : l.append("foo"))

        with check50.internal.register:
            self.assertEqual(l, [])

        self.assertEqual(l, ["foo"])

        with check50.internal.register:
            self.assertEqual(l, ["foo"])

        self.assertEqual(l, ["foo"])
        check50.internal.check_running = False

class TestRegisterAfterEvery(unittest.TestCase):
    def test_after_every(self):
        l = []
        check50.internal.register.after_every(lambda : l.append("foo"))

        with check50.internal.register:
            self.assertEqual(l, [])

        self.assertEqual(l, ["foo"])

        with check50.internal.register:
            self.assertEqual(l, ["foo"])

        self.assertEqual(l, ["foo", "foo"])

class TestRegisterBeforeEvery(unittest.TestCase):
    def test_before_every(self):
        l = []
        check50.internal.register.before_every(lambda : l.append("foo"))

        with check50.internal.register:
            self.assertEqual(l, ["foo"])

        with check50.internal.register:
            self.assertEqual(l, ["foo", "foo"])

        self.assertEqual(l, ["foo", "foo"])


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(module=sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
