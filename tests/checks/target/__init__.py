import check50

@check50.check()
def exists1():
    """foo.py exists"""
    check50.exists("foo.py")

@check50.check()
def exists2():
    """foo.py exists"""
    check50.exists("foo.py")

@check50.check(exists1)
def exists3():
    """foo.py exists"""
    check50.exists("foo.py")


@check50.check()
def exists4():
    """foo.py exists"""
    raise check50.Failure()

@check50.check(exists4)
def exists5():
    """foo.py exists"""
    check50.exists("foo.py")
