# ENABLE_CHECK50_ASSERT = 1
import check50

@check50.check()
def foo():
    stdout = "Hello, world!"
    try:
        assert stdout is "Beautiful is better than ugly."
    except check50.Failure:
        pass

    try:
        assert stdout is "Explicit is better than implicit.", "help msg goes here"
    except check50.Failure:
        pass

    try:
        assert stdout == "Simple is better than complex."
    except check50.Mismatch:
        pass

    try:
        assert stdout in "Complex is better than complicated."
    except check50.Missing:
        pass

    try:
        assert stdout in "Flat is better than nested." check50.Mismatch("Flat is better than nested.", stdout)
    except check50.Mismatch:
        pass

    try:
        assert bar(qux()) in "Readability counts."
    except check50.Missing:
        pass


def bar(baz):
    return "Hello, world!"

def qux():
    return
