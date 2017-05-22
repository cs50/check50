import unittest
import os
import pexpect
import sys

sys.path.append(os.getcwd())
from check50 import Test

class Credit(Test):

    @classmethod
    def tearDownClass(self):
        if os.path.isfile("credit"):
            pexpect.run("rm credit")

    def exists(self):
        """credit.c exists."""
        self.check_exists("credit.c")
    
    def compiles(self):
        """credit.c compiles."""
        self.assert_exists()
        self.check_compiles("clang -o credit credit.c -lcs50")

    def test1(self):
        """identifies 378282246310005 as AMEX"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        child.sendline("378282246310005")
        output = self.output(child)
        self.assertEqual(output, "AMEX\n")

    def test2(self):
        """identifies 371449635398431 as AMEX"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        child.sendline("371449635398431")
        output = self.output(child)
        self.assertEqual(output, "AMEX\n")

    def test3(self):
        """identifies 5555555555554444 as MASTERCARD"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        child.sendline("5555555555554444")
        output = self.output(child)
        self.assertEqual(output, "MASTERCARD\n")

    def test4(self):
        """identifies 5105105105105100 as MASTERCARD"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        child.sendline("5105105105105100")
        output = self.output(child)
        self.assertEqual(output, "MASTERCARD\n")

    def test5(self):
        """identifies 4111111111111111 as VISA"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        child.sendline("4111111111111111")
        output = self.output(child)
        self.assertEqual(output, "VISA\n")

    def test6(self):
        """identifies 4012888888881881 as VISA"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        child.sendline("4012888888881881")
        output = self.output(child)
        self.assertEqual(output, "VISA\n")

    def test7(self):
        """identifies 1234567890 as INVALID"""
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        child.sendline("1234567890")
        output = self.output(child)
        self.assertEqual(output, "INVALID\n")

    def test_reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        self.check_reject(child, "foo")

    def test_reject_empty(self):
        """rejects a non-numeric input of "" """
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./credit")
        child.expect(".+")
        self.check_reject(child, "")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(Credit("exists"))
    suite.addTest(Credit("compiles"))
    suite.addTest(Credit("test1"))
    suite.addTest(Credit("test2"))
    suite.addTest(Credit("test3"))
    suite.addTest(Credit("test4"))
    suite.addTest(Credit("test5"))
    suite.addTest(Credit("test6"))
    suite.addTest(Credit("test7"))
    suite.addTest(Credit("test_reject_foo"))
    suite.addTest(Credit("test_reject_empty"))
    return suite
