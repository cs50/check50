import os
import sys

sys.path.append(os.getcwd())
from check50 import File, Test, check

class MarioLess(Test):
    
    @check()
    def exists(self):
        """mario.c exists."""
        super().exists("mario.c")
    
    @check("exists")
    def compiles(self):
        """mario.c compiles."""
        self.spawn("clang -o mario mario.c -lcs50").exit(0)

    @check("exists", "compiles")
    def test_reject_negative(self):
        """rejects a height of -1"""
        self.spawn("./mario").stdin("-1").reject().kill()

    @check("exists", "compiles")
    def test0(self):
        """handles a height of 0 correctly"""
        self.spawn("./mario").stdin("0").stdout(File("outputs/mario/less/0.txt")).exit(0)

    @check("exists", "compiles")
    def test1(self):
        """handles a height of 1 correctly"""
        self.spawn("./mario").stdin("1").stdout(File("outputs/mario/less/1.txt")).exit(0)

    @check("exists", "compiles")
    def test2(self):
        """handles a height of 2 correctly"""
        self.spawn("./mario").stdin("2").stdout(File("outputs/mario/less/2.txt")).exit(0)

    @check("exists", "compiles")
    def test23(self):
        """handles a height of 23 correctly"""
        self.spawn("./mario").stdin("23").stdout(File("outputs/mario/less/23.txt")).exit(0)

    @check("exists", "compiles")
    def test24(self):
        """rejects a height of 24, and then accepts a height of 2"""
        self.spawn("./mario").stdin("24").reject()\
            .stdin("2").stdout(File("outputs/mario/less/2.txt")).exit(0)
    
    @check("exists", "compiles")
    def test_reject_foo(self):
        """rejects a non-numeric height of "foo" """
        self.spawn("./mario").stdin("foo").reject().kill()

    @check("exists", "compiles")
    def test_reject_empty(self):
        """rejects a non-numeric height of "" """
        self.spawn("./mario").stdin("").reject().kill()
