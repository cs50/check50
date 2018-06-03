import re

from check50 import *

class Hello(Checks):

    @check()
    def exists(self):
        """hello.c exists."""
        self.require("hello.py")

    @check("exists")
    def prints_hello(self):
        """prints "hello, world\\n" """
        expected = "[Hh]ello, world!?\n"
        self = self.spawn("python3 hello.py").stdout().match(expected)
        self.on(fail).match(expected[-1]).help("Did you forget a newline (\"\\n\") at the end of your printf string?")
        self.on(fail).match(expected.replace(",", "")).help("Did you forget the ,?")
