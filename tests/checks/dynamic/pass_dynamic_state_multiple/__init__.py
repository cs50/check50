import check50

@check50.check(dynamic=True)
def foo():
    """foo"""
    return lambda x : x + 1

@check50.check(foo)
def bar(state):
    """bar"""
    if state(1) != 2:
        raise check.Failure("")

@check50.check(dynamic=True)
def foo2():
    """foo2"""
    return lambda x : x + 2

@check50.check(foo)
def baz(state):
    """baz"""
    if state(1) != 2:
        raise check.Failure("")

@check50.check(foo2)
def bar2(state):
    """bar2"""
    if state(1) != 3:
        raise check.Failure("")
