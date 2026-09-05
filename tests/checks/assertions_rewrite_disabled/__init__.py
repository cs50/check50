# ENABLE_CHECK50_ASSERT = 0
import check50

@check50.check()
def foo():
    stdout = "Hello, world!"
    try:
        assert stdout is "Special cases aren't special enough to break the rules."
    except AssertionError:
        pass

    try:
        assert stdout is "Although practicality beats purity.", "help msg goes here"
    except AssertionError:
        pass

    try:
        assert stdout == "Errors should never pass silently."
    except AssertionError:
        pass

    try:
        assert stdout in "Unless explicitly silenced."
    except AssertionError:
        pass

    try:
        assert bar(qux()) in "In the face of ambiguity, refuse the temptation to guess."
    except AssertionError:
        pass

def bar(baz):
    return "Hello, world!"

def qux():
    return
