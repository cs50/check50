import check50
import check50_js as js


@check50.check()
def exists():
    """add() exists in addition.js"""
    js.function_exists("add", js.interface("addition.js"))


@check50.check(exists)
def height1():
    """10 + 2 = 12"""
    out = js.interface("addition.js").call("add", 10, 2)
    expected = 12
    if out != expected:
        raise check50.Mismatch(expected, out)


@check50.check(exists)
def height3():
    """-3 + 4 = 1"""
    out = js.interface("addition.js").call("add", -3, 4)
    expected = 1
    if out != expected:
        raise check50.Mismatch(expected, out)
