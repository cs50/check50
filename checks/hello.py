import os
import sys

sys.path.append(os.getcwd())
from check50 import TestCase, Error, check

class Hello(TestCase):
    
    @check()
    def exists(self):
        """hello.c exists."""
        super().exists("hello.c")
    
    @check("exists")
    def compiles(self):
        """hello.c compiles."""
        self.spawn("clang -o hello hello.c").exit(0)

    @check("compiles")
    def prints_hello(self):
        """prints "Hello, world!\\n" """
        self.spawn("./hello").stdout("^Hello, world!\n$", "Hello, world!\n")

    @check("compiles")
    def prints_hello_2(self):
        """prints "Hello, world!\\n" """
        out = self.spawn("./hello").stdout()
        desired = "Hello, world!\n"
        if out != desired:
            if out == "Hello, world!":
                raise Error((out, desired), "Did you forget a newline (\"\\n\") at the end of your printf string?")
            else:
                raise Error((out, desired))
