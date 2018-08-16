import check50

@check50.check()
def prints_hello_name():
    """prints hello name"""
    check50.run("python3 foo.py").stdin("bar", prompt=True).stdout("hello bar")
