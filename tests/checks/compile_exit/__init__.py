import check50

@check50.check()
def exit():
    """exit"""
    check50.run("python3 foo.py").exit(0)