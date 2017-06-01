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
        self.spawn("clang -o water water.c -lcs50")

    @check("exists", "compiles")
    def test1(self):
        """1 minute equals 12 bottles."""
        self.check_output("./water", "1", re.compile(".*12.*"))

    @check("exists", "compiles")
    def test2(self):
        """2 minute equals 24 bottles."""
        self.check_output("./water", "2", re.compile(".*24.*"))

    @check("exists", "compiles")
    def test5(self):
        """5 minute equals 60 bottles."""
        self.check_output("./water", "5", re.compile(".*60.*"))

    @check("exists", "compiles")
    def test10(self):
        """10 minute equals 120 bottles."""
        self.check_output("./water", "10", re.compile(".*120.*"))

    @check("exists", "compiles")
    def test_reject_foo(self):
        """rejects "foo" minutes"""
        self.check_reject("./water", "foo")

    @check("exists", "compiles")
    def test_reject_empty(self):
        """rejects "" minutes"""
        self.check_reject("./water", "")

    @check("exists", "compiles")
    def test_reject_123abc(self):
        """rejects "123abc" minutes"""
        self.check_reject("./water", "123abc")

