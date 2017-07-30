from check50 import *

class Hello(Checks):

    @check()
    def exists(self):
        """hello.c exists."""
        self.require("hello.c")

    @check("exists")
    def compiles(self):
        """hello.c compiles."""
        self.spawn("clang -o hello hello.c").exit(0)

    @check("compiles")
    def prints_hello(self):
        """prints "Hello, world!\\n" """
        self.spawn("./hello").stdout("Hello, world!\n").exit(0)

    @check("compiles")
    def prints_hello_2(self):
        """prints "Hello, world!\\n" """
        expected = "Hello, world!\n"
        actual = self.spawn("./hello").stdout()
        if out != desired:
            err = Error(Mismatch(expected, actual))
            if out == "Hello, world!":
                err.helpers = "Did you forget a newline (\"\\n\") at the end of your printf string?"
            raise err
