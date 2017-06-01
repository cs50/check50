import os
import sys

sys.path.append(os.getcwd())
from check50 import Test, check

class Hello(Test):
    
    @check()
    def exists(self):
        """hello.c exists."""
        self.check_exists("hello.c")
    
    @check("exists")
    def compiles(self):
        """hello.c compiles."""
        self.check_compiles("clang -o hello hello.c")

    @check("exists", "compiles")
    def prints_hello(self):
        """prints "Hello, world!\\n" """
        self.check_output("./hello", None, "Hello, world!\n")

test_cases = Test.test_cases
remove = ["hello"]
