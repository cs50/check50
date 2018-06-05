import check50
import check50.c

@check50.check()
def exists():
    """hello.c exists"""
    check50.require("hello.c")

@check50.check() # < dependencies aren't ordered yet
def compiles():
    """hello.c compiles"""
    check50.c.compile("hello.c")

@check50.check() # < dependencies aren't ordered yet
def valgrind_hello():
    """valgrinding "hello, world\\n" """
    check50.c.valgrind("./hello").stdout("[H|h]ello, world!?")
