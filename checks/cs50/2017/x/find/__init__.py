from check50 import *


class Find(Checks):

    @check()
    def exists(self):
        """helpers.c exists."""
        self.require("helpers.c")

    @check("exists")
    def compiles(self):
        """helpers.c compiles."""
        self.add("helpers.h")
        self.add("find.c")
        self.spawn("clang -ggdb3 -O0 -std=c99 -Wall -o find find.c helpers.c -lcs50 -lm").exit(0)

    @check("compiles")
    def first_among_three(self):
        """finds 28 in {28,29,30}"""
        self.spawn("./find 28").stdin("28").stdin("29").stdin("30").stdin(EOF).exit(0)

    @check("compiles")
    def second_among_three(self):
        """finds 28 in {27,28,29}"""
        self.spawn("./find 28").stdin("27").stdin("28").stdin("29").stdin(EOF).exit(0)

    @check("compiles")
    def third_among_three(self):
        """finds 28 in {26,27,28}"""
        self.spawn("./find 28").stdin("26").stdin("27").stdin("28").stdin(EOF).exit(0)

    @check("compiles")
    def second_among_four(self):
        """finds 28 in {27,28,29,30}"""
        self.spawn("./find 28").stdin("27").stdin("28").stdin("29").stdin("30").stdin(EOF).exit(0)

    @check("compiles")
    def third_among_four(self):
        """finds 28 in {26,27,28,29}"""
        self.spawn("./find 28").stdin("26").stdin("27").stdin("28").stdin("29").stdin(EOF).exit(0)

    @check("compiles")
    def fourth_among_four(self):
        """finds 28 in {25,26,27,28}"""
        self.spawn("./find 28").stdin("25").stdin("26").stdin("27").stdin("28").stdin(EOF).exit(0)

    @check("compiles")
    def not_among_three(self):
        """doesn't find 28 in {25,26,27}"""
        self.spawn("./find 28").stdin("25").stdin("26").stdin("27").stdin(EOF).exit(1)

    @check("compiles")
    def not_among_four(self):
        """doesn't find 28 in {25,26,27,29}"""
        self.spawn("./find 28").stdin("25").stdin("26").stdin("27").stdin("29").stdin(EOF).exit(1)

    @check("compiles")
    def correctly_sorts(self):
        """finds 28 in {30,27,28,26}"""
        self.spawn("./find 28").stdin("30").stdin("27").stdin("28").stdin("26").stdin(EOF).exit(0)
