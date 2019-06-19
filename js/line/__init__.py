import check50
import check50_js as js


@check50.check()
def exists():
    """line() exists in line.js"""
    js.function_exists("line", js.interface("line.js"))


@check50.check(exists)
def height1():
    """handles a length of 1 correctly"""
    with js.capture_stdout() as stdout:
        js.interface("line.js").call("line", 1)

    actual = stdout.getvalue()
    expected = "#\n"
    if actual != expected:
        raise check50.Mismatch(expected, actual)


@check50.check(exists)
def height3():
    """handles a length of 3 correctly"""
    with js.capture_stdout() as stdout:
        js.interface("line.js").call("line", 3)

    actual = stdout.getvalue()
    expected = "###\n"
    if actual != expected:
        raise check50.Mismatch(expected, actual)
