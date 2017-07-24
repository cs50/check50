import os
import sys

sys.path.append(os.getcwd())
from check50 import *


class MarioLess(Checks):

    @check()
    def exists(self):
        """mario.py exists."""
        super(MarioLessPython, self).exists("mario.py")

    @check("exists")
    def test_reject_negative(self):
        """rejects a height of -1"""
        self.spawn("python3 mario.py").stdin("-1").reject().kill()

    @check("exists")
    def test0(self):
        """handles a height of 0 correctly"""
        self.spawn("python3 mario.py").stdin("0").stdout(File("0.txt")).exit(0)

    @check("exists")
    def test1(self):
        """handles a height of 1 correctly"""
        out = self.spawn("python3 mario.py").stdin("1").stdout()
        correct = File("1.txt").read()
        check_pyramid(out, correct)

    @check("exists")
    def test2(self):
        """handles a height of 2 correctly"""
        out = self.spawn("python3 mario.py").stdin("2").stdout()
        correct = File("2.txt").read()
        check_pyramid(out, correct)

    @check("exists")
    def test23(self):
        """handles a height of 23 correctly"""
        out = self.spawn("python3 mario.py").stdin("23").stdout()
        correct = File("23.txt").read()
        check_pyramid(out, correct)

    @check("exists")
    def test24(self):
        """rejects a height of 24, and then accepts a height of 2"""
        self.spawn("python3 mario.py").stdin("24").reject()\
            .stdin("2").stdout(File("2.txt")).exit(0)

    @check("exists")
    def test_reject_foo(self):
        """rejects a non-numeric height of "foo" """
        self.spawn("python3 mario.py").stdin("foo").reject()

    @check("exists")
    def test_reject_empty(self):
        """rejects a non-numeric height of "" """
        self.spawn("python3 mario.py").stdin("").reject()

def check_pyramid(output, correct):
    if output == correct:
        return

    output = output.split("\n")
    correct = correct.split("\n")

    if len(output) != len(correct):
        raise Error((output, correct))

    # check for trailing whitespace
    helper = "Did you add too much trailing whitespace to the end of your pyramid?"
    for out_line, correct_line in zip(output, correct)
        if out_line.rstrip() != correct_line:
            helper = None
            break
    raise Error((output, correct), helper)
