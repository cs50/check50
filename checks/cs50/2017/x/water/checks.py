import os
import re
import sys

sys.path.append(os.getcwd())
from check50 import TestCase, check

class Water(TestCase):

    @check()
    def exists(self):
        """water.c exists."""
        super().exists("water.c")
    
    @check("exists")
    def compiles(self):
        """water.c compiles."""
        self.spawn("clang -o water water.c -lcs50").exit(0)

    @check("compiles")
    def test1(self):
        """1 minute equals 12 bottles."""
        self.spawn("./water").stdin("1").stdout("^.*12.*$", 12)

    @check("compiles")
    def test2(self):
        """2 minute equals 24 bottles."""
        self.spawn("./water").stdin("2").stdout("^.*24.*$", 24)

    @check("compiles")
    def test5(self):
        """5 minute equals 60 bottles."""
        self.spawn("./water").stdin("5").stdout("^.*60.*$", 60).exit(0)

    @check("compiles")
    def test10(self):
        """10 minute equals 120 bottles."""
        self.spawn("./water").stdin("10").stdout("^.*120.*$", 120).exit(0)

    @check("compiles")
    def test_reject_foo(self):
        """rejects "foo" minutes"""
        self.spawn("./water").stdin("foo").reject()

    @check("compiles")
    def test_reject_empty(self):
        """rejects "" minutes"""
        self.spawn("./water").stdin("").reject()

    @check("compiles")
    def test_reject_123abc(self):
        """rejects "123abc" minutes"""
        self.spawn("./water").stdin("123abc").reject()
