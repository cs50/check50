import os
import sys
import subprocess

sys.path.append(os.getcwd())
from check50 import *

class MarioLessPython(TestCase):

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
        """mario.py exists."""
        super(MarioLessPython, self).exists("mario.py")

    @check("exists")
    def test_reject_negative(self):
        """rejects a height of -1"""
        self.include("cs50.py")
        self.spawn("python3 mario.py").stdin("-1").reject().kill()

    # @check("exists")
    # def test0(self):
    #     """handles a height of 0 correctly"""
    #     self.include("cs50.py")
    #     self.spawn("python mario.py").stdin("0").stdout(File("0.txt")).exit(0)
    #     subprocess.call("bash", shell=True)
    #
    # @check("exists")
    # def test1(self):
    #     """handles a height of 1 correctly"""
    #     self.include("cs50.py")
    #     out = self.spawn("python mario.py").stdin("1").stdout().split("\n")
    #     correct = self.checkfile("1.txt").split("\n")
    #     self.check_pyramid(out, correct)
    #
    # @check("exists")
    # def test2(self):
    #     """handles a height of 2 correctly"""
    #     self.include("cs50.py")
    #     out = self.spawn("python mario.py").stdin("2").stdout().split("\n")
    #     correct = self.checkfile("2.txt").split("\n")
    #     self.check_pyramid(out, correct)
    #
    # @check("exists")
    # def test23(self):
    #     """handles a height of 23 correctly"""
    #     self.include("cs50.py")
    #     out = self.spawn("python mario.py").stdin("23").stdout().split("\n")
    #     correct = self.checkfile("23.txt").split("\n")
    #     self.check_pyramid(out, correct)
    #
    # @check("exists")
    # def test24(self):
    #     """rejects a height of 24, and then accepts a height of 2"""
    #     self.include("cs50.py")
    #     self.spawn("python mario.py").stdin("24").reject()\
    #         .stdin("2").stdout(File("2.txt")).exit(0)
    #
    # @check("exists")
    # def test_reject_foo(self):
    #     """rejects a non-numeric height of "foo" """
    #     self.include("cs50.py")
    #     self.spawn("python mario.py").stdin("foo").reject()
    #
    # @check("exists")
    # def test_reject_empty(self):
    #     """rejects a non-numeric height of "" """
    #     self.include("cs50.py")
    #     self.spawn("python mario.py").stdin("").reject()
