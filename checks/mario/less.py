import unittest
import os
import pexpect
import sys

sys.path.append(os.getcwd())
from check50 import Test

class MarioLess(Test):

    @classmethod
    def tearDownClass(self):
        if os.path.isfile("mario"):
            pexpect.run("rm mario")

    def exists(self):
        """mario.c exists."""
        self.check_exists("mario.c")
    
    def compiles(self):
        """mario.c compiles."""
        self.assert_exists()
        self.check_compiles("clang -o mario mario.c -lcs50")

    def test_reject_negative(self):
        """rejects a height of -1"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./mario")
        child.expect(".+")
        self.check_reject(child, "-1")

    def test0(self):
        """handles a height of 0 correctly"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./mario")
        child.expect(".+")
        child.sendline("0")
        output = self.output(child)
        self.assert_matches(output, "outputs/mario-less/0.txt")

    def test1(self):
        """handles a height of 1 correctly"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./mario")
        child.expect(".+")
        child.sendline("1")
        output = self.output(child)
        self.assert_matches(output, "outputs/mario-less/1.txt")

    def test2(self):
        """handles a height of 2 correctly"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./mario")
        child.expect(".+")
        child.sendline("2")
        output = self.output(child)
        self.assert_matches(output, "outputs/mario-less/2.txt")

    def test23(self):
        """handles a height of 23 correctly"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./mario")
        child.expect(".+")
        child.sendline("23")
        output = self.output(child)
        self.assert_matches(output, "outputs/mario-less/23.txt")

    def test24(self):
        """rejects a height of 24, and then accepts a height of 2"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./mario")
        child.expect(".+")
        self.check_reject(child, "24")
        child.expect(".+")
        child.sendline("2")
        output = self.output(child)
        self.assert_matches(output, "outputs/mario-less/2.txt")

    def test_reject_foo(self):
        """rejects a non-numeric height of "foo" """
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./mario")
        child.expect(".+")
        self.check_reject(child, "foo")

    def test_reject_empty(self):
        """rejects a non-numeric height of "" """
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./mario")
        child.expect(".+")
        self.check_reject(child, "")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(MarioLess("exists"))
    suite.addTest(MarioLess("compiles"))
    suite.addTest(MarioLess("test_reject_negative"))
    suite.addTest(MarioLess("test0"))
    suite.addTest(MarioLess("test1"))
    suite.addTest(MarioLess("test2"))
    suite.addTest(MarioLess("test23"))
    suite.addTest(MarioLess("test24"))
    suite.addTest(MarioLess("test_reject_foo"))
    suite.addTest(MarioLess("test_reject_empty"))
    return suite
