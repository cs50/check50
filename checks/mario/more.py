import os
import sys

sys.path.append(os.getcwd())
from check50 import File, Test, check

class MarioMore(Test):

    @check()
    def exists(self):
        """mario.c exists."""
        self.check_exists("mario.c")
    
    @check("exists")
    def compiles(self):
        """mario.c compiles."""
        self.check_compiles("clang -o mario mario.c -lcs50")

    @check("exists", "compiles")
    def test_reject_negative(self):
        """rejects a height of -1"""
        self.check_reject("./mario", "-1")

    @check("exists", "compiles")
    def test0(self):
        """handles a height of 0 correctly"""
        self.check_output("./mario", "0", File("outputs/mario-more/0.txt"))

    @check("exists", "compiles")
    def test1(self):
        """handles a height of 1 correctly"""
        self.check_output("./mario", "1", File("outputs/mario-more/1.txt"))

    @check("exists", "compiles")
    def test2(self):
        """handles a height of 2 correctly"""
        self.check_output("./mario", "2", File("outputs/mario-more/2.txt"))

    @check("exists", "compiles")
    def test23(self):
        """handles a height of 23 correctly"""
        self.check_output("./mario", "23", File("outputs/mario-more/23.txt"))

    @check("exists", "compiles")
    def test24(self):
        """rejects a height of 24, and then accepts a height of 2"""
        self.check_output("./mario", ["24", "2"], File("outputs/mario-more/2.txt"))

    @check("exists", "compiles")
    def test_reject_foo(self):
        """rejects a non-numeric height of "foo" """
        self.check_reject("./mario", "foo")

    @check("exists", "compiles")
    def test_reject_empty(self):
        """rejects a non-numeric height of "" """
        self.check_reject("./mario", "")

test_cases = Test.test_cases
remove = ["mario"]
