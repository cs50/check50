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
        self.spawn("clang -o greedy greedy.c -lcs50")

    @check("exists", "compiles")
    def test1(self):
        """input of 0.41 yields output of 4"""
        self.check_output("./greedy", "0.41", "4\n")

    @check("exists", "compiles")
    def test2(self):
        """input of 0.01 yields output of 1"""
        self.check_output("./greedy", "0.01", "1\n")

    @check("exists", "compiles")
    def test3(self):
        """input of 0.15 yields output of 2"""
        self.check_output("./greedy", "0.15", "2\n")

    @check("exists", "compiles")
    def test4(self):
        """input of 1.6 yields output of 7"""
        self.check_output("./greedy", "1.6", "7\n")

    @check("exists", "compiles")
    def test5(self):
        """input of 23 yields output of 92"""
        self.check_output("./greedy", "23", "92\n")

    @check("exists", "compiles")
    def test6(self):
        """input of 4.2 yields output of 18"""
        self.check_output("./greedy", "4.2", "18\n")

    @check("exists", "compiles")
    def test_reject_negative(self):
        """rejects a negative input like -.1"""
        self.check_reject("./greedy", "-.1")

    @check("exists", "compiles")
    def test_reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.check_reject("./greedy", "foo")

    @check("exists", "compiles")
    def test_reject_empty(self):
        """rejects a non-numeric input of "" """
        self.check_reject("./greedy", "")

