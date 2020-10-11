import check50

@check50.check()
def exists():
    """foo.py exists"""
    check50.exists("foo.py")

@check50.check(exists)
def takes_input():
    """takes input"""
    check50.run("python3 foo.py").stdin("aaa", prompt=False, str_line="bbb")
