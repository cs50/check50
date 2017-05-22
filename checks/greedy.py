import unittest
import os
import pexpect
import sys

sys.path.append(os.getcwd())
from check50 import Test

class Greedy(Test):

    @classmethod
    def tearDownClass(self):
        if os.path.isfile("greedy"):
            pexpect.run("rm greedy")

    def setUp(self):
        print("setting up... " + self._testMethodName)

    def exists(self):
        """greedy.c exists."""
        self.check_exists("greedy.c")
    
    def compiles(self):
        """greedy.c compiles."""
        self.assert_exists()
        self.check_compiles("clang -o greedy greedy.c -lcs50")

    def test1(self):
        """input of 0.41 yields output of 4"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        try:
            child.expect(".+", timeout=2)
        except:
            self.fail()
        child.sendline("0.41")
        output = self.output(child)
        self.assertEqual(output, "4\n")

    def test2(self):
        """input of 0.01 yields output of 1"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        child.expect(".+")
        child.sendline("0.01")
        output = self.output(child)
        self.assertEqual(output, "1\n")

    def test3(self):
        """input of 0.15 yields output of 2"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        child.expect(".+")
        child.sendline("0.15")
        output = self.output(child)
        self.assertEqual(output, "2\n")

    def test4(self):
        """input of 1.6 yields output of 7"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        child.expect(".+")
        child.sendline("1.6")
        output = self.output(child)
        self.assertEqual(output, "7\n")

    def test5(self):
        """input of 23 yields output of 92"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        child.expect(".+")
        child.sendline("23")
        output = self.output(child)
        self.assertEqual(output, "92\n")

    def test6(self):
        """input of 4.2 yields output of 18"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        child.expect(".+")
        child.sendline("4.2")
        output = self.output(child)
        self.assertEqual(output, "18\n")

    def test_reject_negative(self):
        """rejects a negative input like -.1"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        child.expect(".+")
        self.check_reject(child, "-.1")

    def test_reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        child.expect(".+")
        self.check_reject(child, "foo")

    def test_reject_empty(self):
        """rejects a non-numeric input of "" """
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./greedy")
        child.expect(".+")
        self.check_reject(child, "")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(Greedy("exists"))
    suite.addTest(Greedy("compiles"))
    suite.addTest(Greedy("test1"))
    """
    suite.addTest(Greedy("test2"))
    suite.addTest(Greedy("test3"))
    suite.addTest(Greedy("test4"))
    suite.addTest(Greedy("test5"))
    suite.addTest(Greedy("test6"))
    suite.addTest(Greedy("test_reject_negative"))
    suite.addTest(Greedy("test_reject_foo"))
    suite.addTest(Greedy("test_reject_empty"))
    """
    return suite
