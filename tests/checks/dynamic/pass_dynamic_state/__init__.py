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
