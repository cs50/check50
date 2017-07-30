from check50 import *


class MarioLess(Checks):


    @check()
    def exists(self):
        """mario.c exists."""
        self.require("mario.c")
        self.add("0.txt", "1.txt", "2.txt", "23.txt")

    @check("exists")
    def compiles(self):
        """mario.c compiles."""
        self.spawn("clang -o mario mario.c -lcs50").exit(0)

    @check("compiles")
    def test_reject_negative(self):
        """rejects a height of -1"""
        self.spawn("./mario").stdin("-1").reject()

    @check("compiles")
    def test0(self):
        """handles a height of 0 correctly"""
        self.spawn("./mario").stdin("0").stdout(File("0.txt")).exit(0)

    @check("compiles")
    def test1(self):
        """handles a height of 1 correctly"""
        out = self.spawn("./mario").stdin("1").stdout()
        correct = File("1.txt").read()
        check_pyramid(out, correct)

    @check("compiles")
    def test2(self):
        """handles a height of 2 correctly"""
        out = self.spawn("./mario").stdin("2").stdout()
        correct = File("2.txt").read()
        check_pyramid(out, correct)

    @check("compiles")
    def test23(self):
        """handles a height of 23 correctly"""
        out = self.spawn("./mario").stdin("23").stdout()
        correct = File("23.txt").read()
        check_pyramid(out, correct)

    @check("compiles")
    def test24(self):
        """rejects a height of 24, and then accepts a height of 2"""
        self.spawn("./mario").stdin("24").reject()\
            .stdin("2").stdout(File("2.txt")).exit(0)

    @check("compiles")
    def test_reject_foo(self):
        """rejects a non-numeric height of "foo" """
        self.spawn("./mario").stdin("foo").reject()

    @check("compiles")
    def test_reject_empty(self):
        """rejects a non-numeric height of "" """
        self.spawn("./mario").stdin("").reject()


def check_pyramid(output, correct):
    if output == correct:
        return

    output = output.split("\n")
    correct = correct.split("\n")

    err = Error(Mismatch(output, correct))
    # check if pyramids are the same height and only differ by trailing whitespace
    if len(output) == len(correct) and all(ol.rstrip() == cl for ol, cl in zip(output, correct)):
        err.helpers = "Did you add too much trailing whitespace to the end of your pyramid?"
    raise err
