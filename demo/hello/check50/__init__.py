import check50
import check50.c

@check50.check()
def exists():
    """hello.c exists"""
    check50.require("hello.c")

@check50.check()
def compiles():
    """hello.c compiles"""
    check50.c.compile("hello.c")

@check50.check()
def valgrind_hello():
    """valgrinding "hello, world\\n" """
    check50.c.valgrind("./hello").stdin("david").stdout("[H|h]ello, david!?")
