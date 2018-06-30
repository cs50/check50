import check50

@check50.check()
def exists():
    """foo.py exists"""
    check50.exists("foo.py")

@check50.check(exists)
def prints_hello_name():
    """prints hello name"""
    check50.run("python3 foo.py").stdin("bar", prompt=False).stdout("hello bar")
