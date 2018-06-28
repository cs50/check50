import check50

@check50.check()
def exists():
    """foo.py exists"""
    check50.exists("foo.py")

@check50.check(exists)
def exits():
    """foo.py exits properly"""
    check50.run("python3 foo.py").exit(0)
