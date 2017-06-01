import os
import sys

sys.path.append(os.getcwd())
from check50 import Test, check

class Hello(Test):
    
    @check()
    def exists(self):
        """hello.c exists."""
        super().exists("hello.c")
    
    @check("exists")
    def compiles(self):
        """hello.c compiles."""
        self.spawn("clang -o hello hello.c").exit(0)

    @check("exists", "compiles")
    def prints_hello(self):
        """prints "Hello, world!\\n" """
        self.spawn("./hello").stdout("^Hello, world!\n$").exit(0)
