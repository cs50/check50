from .less import *


class InitialsMore(InitialsLess):

    @check("compiles")
    def space_between(self):
        """Outputs HJ for hailey       James"""
        self.spawn("./initials").stdin("hailey       James", prompt=False).stdout(match("HJ"), "HJ\n").exit(0)

    @check("compiles")
    def space_before_after(self):
        """Outputs HJ for     hailey James    """
        self.spawn("./initials").stdin("    hailey James    ", prompt=False).stdout(match("HJ"), "HJ\n").exit(0)
