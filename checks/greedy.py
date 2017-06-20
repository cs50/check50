import os
import re
import sys

sys.path.append(os.getcwd())
from check50 import TestCase, Error, check

class Greedy(TestCase):
    
    @check()
    def exists(self):
        """greedy.c exists."""
        super().exists("greedy.c")
    
    @check("exists")
    def compiles(self):
        """greedy.c compiles."""
        self.spawn("clang -o greedy greedy.c -lcs50").exit(0)

    @check("compiles")
    def test041(self):
        """input of 0.41 yields output of 4"""
        self.spawn("./greedy").stdin("0.41").stdout("^4\n$", 4).exit(0)

    @check("compiles")
    def test001(self):
        """input of 0.01 yields output of 1"""
        self.spawn("./greedy").stdin("0.01").stdout("^1\n$", 1).exit(0)

    @check("compiles")
    def test015(self):
        """input of 0.15 yields output of 2"""
        self.spawn("./greedy").stdin("0.15").stdout("^2\n$", 2).exit(0)

    @check("compiles")
    def test160(self):
        """input of 1.6 yields output of 7"""
        self.spawn("./greedy").stdin("1.6").stdout("^7\n$", 7).exit(0)

    @check("compiles")
    def test230(self):
        """input of 23 yields output of 92"""
        self.spawn("./greedy").stdin("23").stdout("^92\n$", 92).exit(0)

    @check("compiles")
    def test420(self):
        """input of 4.2 yields output of 18"""
        out = self.spawn("./greedy").stdin("4.2").stdout()
        desired = "18"
        if not re.compile("^18\n$").match(out):
            if re.compile("^22\n$").match(out):
                raise Error((out, desired), "Did you forget to round your input to the nearest cent?")
            else:
                raise Error((out, desired))

    @check("compiles")
    def test_reject_negative(self):
        """rejects a negative input like -.1"""
        self.spawn("./greedy").stdin("-1").reject()

    @check("compiles")
    def test_reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.spawn("./greedy").stdin("foo").reject()

    @check("compiles")
    def test_reject_empty(self):
        """rejects a non-numeric input of "" """
        self.spawn("./greedy").stdin("").reject()

