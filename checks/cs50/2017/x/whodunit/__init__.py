from check50 import *


class Whodunit(Checks):

    @check()
    def exists(self):
        """whodunit.c exists"""
        self.require("whodunit.c")

    @check("exists")
    def compiles(self):
        """whodunit.c compiles"""
        self.add("bmp.h")
        self.spawn("clang -std=c99 -Wall -Werror whodunit.c -o whodunit -lm").exit(0)

    @check("compiles")
    def different(self):
        """whodunit.c alters the image"""
        self.add("clue.bmp")
        self.spawn("./whodunit clue.bmp verdict.bmp").exit()
        if self.hash("verdict.bmp") == self.hash("clue.bmp"):
            raise Error("output image is identical to clue.bmp")
