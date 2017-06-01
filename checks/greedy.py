import os
import sys

sys.path.append(os.getcwd())
from check50 import Test, check

class Greedy(Test):
    
    @check()
    def exists(self):
        """greedy.c exists."""
        super().exists("greedy.c")
    
    @check("exists")
    def compiles(self):
        """greedy.c compiles."""
        self.spawn("clang -o greedy greedy.c -lcs50").exit(0)

    @check("exists", "compiles")
    def test1(self):
        """input of 0.41 yields output of 4"""
        self.spawn("./greedy").stdin("0.41").stdout("^4\n$").exit(0)

    @check("exists", "compiles")
    def test2(self):
        """input of 0.01 yields output of 1"""
        self.spawn("./greedy").stdin("0.01").stdout("^1\n$").exit(0)

    @check("exists", "compiles")
    def test3(self):
        """input of 0.15 yields output of 2"""
        self.spawn("./greedy").stdin("0.15").stdout("^2\n$").exit(0)

    @check("exists", "compiles")
    def test4(self):
        """input of 1.6 yields output of 7"""
        self.spawn("./greedy").stdin("1.6").stdout("^7\n$").exit(0)

    @check("exists", "compiles")
    def test5(self):
        """input of 23 yields output of 92"""
        self.spawn("./greedy").stdin("23").stdout("^92\n$").exit(0)

    @check("exists", "compiles")
    def test6(self):
        """input of 4.2 yields output of 18"""
        self.spawn("./greedy").stdin("4.2").stdout("^18\n$").exit(0)

    @check("exists", "compiles")
    def test_reject_negative(self):
        """rejects a negative input like -.1"""
        self.spawn("./greedy").stdin("-1").reject().kill()

    @check("exists", "compiles")
    def test_reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.spawn("./greedy").stdin("foo").reject().kill()

    @check("exists", "compiles")
    def test_reject_empty(self):
        """rejects a non-numeric input of "" """
        self.spawn("./greedy").stdin("").reject().kill()

