import os
import sys

sys.path.append(os.getcwd())
from check50 import TestCase, Error, check

class Test(TestCase):
    @check()
    def exists(self):
        """test.py exists."""
        super(Test, self).exists("test.py")

    @check("exists")
    def runs(self):
        """test.py runs"""
        self.spawn("python test.py").exit(0)

    @check("runs")
    def prints_hello(self):
        """prints "Hello, world!\\n" """
        self.spawn("python test.py").stdout("^Hello, world!\n$", "Hello, world!\n")
