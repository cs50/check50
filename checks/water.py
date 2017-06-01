import os
import re
import sys

sys.path.append(os.getcwd())
from check50 import Test, check

class Water(Test):

    @check()
    def exists(self):
        """water.c exists."""
        super().exists("water.c")
    
    @check("exists")
    def compiles(self):
        """water.c compiles."""
        self.spawn("clang -o water water.c -lcs50").exit(0)

    @check("exists", "compiles")
    def test1(self):
        """1 minute equals 12 bottles."""
        self.spawn("./water").stdin("1").stdout("^.*12.*$")

    @check("exists", "compiles")
    def test2(self):
        """2 minute equals 24 bottles."""
        self.spawn("./water").stdin("2").stdout("^.*24.*$")

    @check("exists", "compiles")
    def test5(self):
        """5 minute equals 60 bottles."""
        self.spawn("./water").stdin("5").stdout("^.*60.*$").exit(0)

    @check("exists", "compiles")
    def test10(self):
        """10 minute equals 120 bottles."""
        self.spawn("./water").stdin("10").stdout("^.*120.*$").exit(0)

    @check("exists", "compiles")
    def test_reject_foo(self):
        """rejects "foo" minutes"""
        self.spawn("./water").stdin("-1").reject().kill()

    @check("exists", "compiles")
    def test_reject_empty(self):
        """rejects "" minutes"""
        self.spawn("./water").stdin("").reject().kill()

    @check("exists", "compiles")
    def test_reject_123abc(self):
        """rejects "123abc" minutes"""
        self.spawn("./water").stdin("123abc").reject().kill()
