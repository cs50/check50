import re

from check50 import *


@checks
class Greedy(Checks):

    @check()
    def exists(self):
        """greedy compiles."""
        self.require("greedy.c")

    @check("exists")
    def compiles(self):
        """greedy compiles"""
        self.spawn("clang -ggdb3 -o greedy greedy.c -lcs50 -lm").exit(0)

    @check("compiles")
    def test041(self):
        """input of 0.41 yields output of 4"""
        self.spawn("./greedy").stdin("0.41").stdout(coins(4), 4).exit(0)

    @check("compiles")
    def test001(self):
        """input of 0.01 yields output of 1"""
        self.spawn("./greedy").stdin("0.01").stdout(coins(1), 1).exit(0)

    @check("compiles")
    def test015(self):
        """input of 0.15 yields output of 2"""
        self.spawn("./greedy").stdin("0.15").stdout(coins(2), 2).exit(0)

    @check("compiles")
    def test160(self):
        """input of 1.6 yields output of 7"""
        self.spawn("./greedy").stdin("1.6").stdout(coins(6), 6).exit(0)

    @check("compiles")
    def test230(self):
        """input of 23 yields output of 92"""
        self.spawn("./greedy").stdin("23").stdout(coins(92), 92).exit(0)

    @check("compiles")
    def test420(self):
        """input of 4.2 yields output of 18"""
        expected = "18"
        actual = self.spawn("./greedy").stdin("4.2").stdout()
        if not re.compile(coins(18)).match(out):
            err = Error(Mismatch(expected, actual))
            if re.compile(coins(22)).match(out):
                err.helpers = "Did you forget to round your input to the nearest cent?"
            raise err

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


def coins(num):
    return r"(^|[^\d]){}(?!\d)".format(num)
