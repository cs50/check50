from check50 import *


class Water(Checks):

    @check()
    def exists(self):
        """water.c exists."""
        self.require("water.c")

    @check("exists")
    def compiles(self):
        """water.c compiles."""
        self.spawn("clang -o water water.c -lcs50").exit(0)

    @check("compiles")
    def test1(self):
        """1 minute equals 12 bottles."""
        self.spawn("./water").stdin("1").stdout(bottles(12), "12\n")

    @check("compiles")
    def test2(self):
        """2 minute equals 24 bottles."""
        self.spawn("./water").stdin("2").stdout(bottles(24), "24\n")

    @check("compiles")
    def test5(self):
        """5 minute equals 60 bottles."""
        self.spawn("./water").stdin("5").stdout(bottles(60), "60\n").exit(0)

    @check("compiles")
    def test10(self):
        """10 minute equals 120 bottles."""
        self.spawn("./water").stdin("10").stdout(bottles(120), "120\n").exit(0)

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


def bottles(num):
    return "(^|[^\d]){}[^\d]".format(num)
