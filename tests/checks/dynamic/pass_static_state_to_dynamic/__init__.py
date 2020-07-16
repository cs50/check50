import check50

@check50.check()
def foo():
    """foo"""
    return "baz"

@check50.check(foo, dynamic=True)
def bar(state):
    """bar"""
    if state != "baz":
        raise check.Failure("")
