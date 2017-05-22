import unittest
import os
import pexpect
import sys

sys.path.append(os.getcwd())
from check50 import Test

class Water(Test):

    @classmethod
    def tearDownClass(self):
        if os.path.isfile("water"):
            pexpect.run("rm water")

    def exists(self):
        """water.c exists."""
        self.check_exists("water.c")
    
    def compiles(self):
        """water.c compiles."""
        self.assert_exists()
        self.check_compiles("clang -o water water.c -lcs50")

    def test1(self):
        """1 minute equals 12 bottles."""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./water")
        child.sendline("1")
        output = self.output(child)
        self.assertTrue("12" in output)

    def test2(self):
        """2 minute equals 24 bottles."""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./water")
        child.sendline("2")
        output = self.output(child)
        self.assertTrue("24" in output)

    def test5(self):
        """5 minute equals 60 bottles."""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./water")
        child.sendline("5")
        output = self.output(child)
        self.assertTrue("60" in output)

    def test10(self):
        """10 minute equals 120 bottles."""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./water")
        child.sendline("10")
        output = self.output(child)
        self.assertTrue("120" in output)

    def test_reject_foo(self):
        """rejects "foo" minutes"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./water")
        self.check_reject(child, "foo")

    def test_reject_empty(self):
        """rejects "" minutes"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./water")
        self.check_reject(child, "")

    def test_reject_123abc(self):
        """rejects "123abc" minutes"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./water")
        self.check_reject(child, "123abc")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(Water("exists"))
    suite.addTest(Water("compiles"))
    suite.addTest(Water("test1"))
    suite.addTest(Water("test2"))
    suite.addTest(Water("test5"))
    suite.addTest(Water("test10"))
    suite.addTest(Water("test_reject_foo"))
    suite.addTest(Water("test_reject_empty"))
    suite.addTest(Water("test_reject_123abc"))
    return suite
