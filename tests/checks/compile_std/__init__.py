import check50

@check()
def std():
    """std"""
    check50.run("python3 foo.py").stdin("bar").stdout("bar", regex=False).exit(0)