import os
import sys

sys.path.append(os.getcwd())
from check50 import File, TestCase, Error, check


class MarioMore(TestCase):

    def check_pyramid(self, output, correct):
        if output == correct:
            return 1
        if len(output) != len(correct):
            raise Error((output, correct))

        # check for trailing whitespace
        match = True 
        for i in range(len(output)):
            if output[i].rstrip() != correct[i]:
                match = False
        if match:
            raise Error((output, correct), "Did you add too much trailing whitespace to the end of your pyramid?")
        raise Error((output, correct))
    
    @check()
    def exists(self):
        """mario.c exists."""
        super().exists("mario.c")
    
    @check("exists")
    def compiles(self):
        """mario.c compiles."""
        self.spawn("clang -o mario mario.c -lcs50").exit(0)

    @check("compiles")
    def test_reject_negative(self):
        """rejects a height of -1"""
        self.spawn("./mario").stdin("-1").reject().kill()

    @check("compiles")
    def test0(self):
        """handles a height of 0 correctly"""
        self.spawn("./mario").stdin("0").stdout(File("outputs/mario/more/0.txt")).exit(0)

    @check("compiles")
    def test1(self):
        """handles a height of 1 correctly"""
        out = self.spawn("./mario").stdin("1").stdout().split("\n")
        correct = self.checkfile("outputs/mario/more/1.txt").split("\n")
        self.check_pyramid(out, correct)

    @check("compiles")
    def test2(self):
        """handles a height of 2 correctly"""
        out = self.spawn("./mario").stdin("2").stdout().split("\n")
        correct = self.checkfile("outputs/mario/more/2.txt").split("\n")
        self.check_pyramid(out, correct)

    @check("compiles")
    def test23(self):
        """handles a height of 23 correctly"""
        out = self.spawn("./mario").stdin("23").stdout().split("\n")
        correct = self.checkfile("outputs/mario/more/23.txt").split("\n")
        self.check_pyramid(out, correct)

    @check("compiles")
    def test24(self):
        """rejects a height of 24, and then accepts a height of 2"""
        self.spawn("./mario").stdin("24").reject()\
            .stdin("2").stdout(File("outputs/mario/more/2.txt")).exit(0)
    
    @check("compiles")
    def test_reject_foo(self):
        """rejects a non-numeric height of "foo" """
        self.spawn("./mario").stdin("foo").reject()

    @check("compiles")
    def test_reject_empty(self):
        """rejects a non-numeric height of "" """
        self.spawn("./mario").stdin("").reject()
