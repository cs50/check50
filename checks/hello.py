import unittest
import os
import pexpect
import sys

sys.path.append(os.getcwd())
from check50 import Test

class Hello(Test):

    @classmethod
    def tearDownClass(self):
        if os.path.isfile("hello"):
            pexpect.run("rm hello")

    def exists(self):
        """hello.c exists."""
        self.check_exists("hello.c")
    
    def compiles(self):
        """hello.c compiles."""
        self.assert_exists()
        self.check_compiles("clang -o hello hello.c")

    def prints_hello(self):
        """prints "Hello, world!\n" """
        self.assert_exists()
        self.assert_compiles()
        child = self.spawn("./hello")
        output = self.output(child)
        self.assertEqual(output, "Hello, world!\n")

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(Hello("exists"))
    suite.addTest(Hello("compiles"))
    suite.addTest(Hello("prints_hello"))
    return suite
