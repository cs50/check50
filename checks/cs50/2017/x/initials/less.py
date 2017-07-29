from check50 import *


@checks
class InitialsLess(Checks):

    @check()
    def exists(self):
        """initials.c exists."""
        self.require("initials.c")

    @check("exists")
    def compiles(self):
        """initials.c compiles."""
        self.spawn("clang -o initials initials.c -lcs50").exit(0)

    @check("compiles")
    def uppercase(self):
        """Outputs HLJ for Hailey Lynn James"""
        self.spawn("./initials").stdin("Hailey Lynn James", prompt=False).stdout(match("HLJ"), "HLJ\n").exit(0)

    @check("compiles")
    def lowercase(self):
        """Outputs HLJ for hailey lynn james"""
        self.spawn("./initials").stdin("hailey lynn james", prompt=False).stdout(match("HLJ"), "HLJ\n").exit(0)

    @check("compiles")
    def mixed_case(self):
        """Outputs HJ for hailey James"""
        self.spawn("./initials").stdin("hailey James", prompt=False).stdout(match("HJ"), "HJ\n").exit(0)

    @check("compiles")
    def all_uppercase(self):
        """Outputs B for BRIAN"""
        self.spawn("./initials").stdin("BRIAN", prompt=False).stdout(match("B"), "B\n").exit(0)


def match(initials):
    return "^(.*\n)?{}\n".format(initials)
