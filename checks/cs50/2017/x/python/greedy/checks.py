import os
import re
import sys

sys.path.append(os.getcwd())
from check50 import *

class GreedyPython(TestCase):

    @check()
    def exists(self):
        """greedy.py exists."""
        self.include("cs50.py")
        super(GreedyPython, self).exists("greedy.py")

    @check("exists")
    def test041(self):
        """input of 0.41 yields output of 4"""
        self.include("cs50.py")
        self.spawn("python3 greedy.py").stdin("0.41").stdout(coins(4), 4).exit(0)

    @check("exists")
    def test001(self):
        """input of 0.01 yields output of 1"""
        self.include("cs50.py")
        self.spawn("python3 greedy.py").stdin("0.01").stdout(coins(1), 1).exit(0)

    @check("exists")
    def test015(self):
        """input of 0.15 yields output of 2"""
        self.include("cs50.py")
        self.spawn("python3 greedy.py").stdin("0.15").stdout(coins(2), 2).exit(0)

    @check("exists")
    def test160(self):
        """input of 1.6 yields output of 7"""
        self.include("cs50.py")
        self.spawn("python3 greedy.py").stdin("1.6").stdout(coins(6), 6).exit(0)

    @check("exists")
    def test230(self):
        """input of 23 yields output of 92"""
        self.include("cs50.py")
        self.spawn("python3 greedy.py").stdin("23").stdout(coins(92), 92).exit(0)

    @check("exists")
    def test420(self):
        """input of 4.2 yields output of 18"""
        self.include("cs50.py")
        out = self.spawn("python3 greedy.py").stdin("4.2").stdout()
        desired = "18"
        if not re.compile(coins(18)).match(out):
            if re.compile(coins(22)).match(out):
                raise Error((out, desired), "Did you forget to round your input to the nearest cent?")
            else:
                raise Error((out, desired))

    @check("exists")
    def test_reject_negative(self):
        """rejects a negative input like -.1"""
        self.include("cs50.py")
        self.spawn("python3 greedy.py").stdin("-1").reject()

    @check("exists")
    def test_reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.include("cs50.py")
        self.spawn("python3 greedy.py").stdin("foo").reject()

    @check("exists")
    def test_reject_empty(self):
        """rejects a non-numeric input of "" """
        self.include("cs50.py")
        self.spawn("python3 greedy.py").stdin("").reject()


def coins(num):
    return r"(^|[^\d]){}(?!\d)".format(num)
