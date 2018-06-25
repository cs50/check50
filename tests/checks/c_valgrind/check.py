import check50
import check50.c

@check50.check()
def val():
    """valgrind foo"""
    check50.c.compile("foo.c")
    check50.c.valgrind("./foo")
