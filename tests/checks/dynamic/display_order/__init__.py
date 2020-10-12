import check50

@check50.check(dynamic=True)
def foo():
    """foo"""
    @check50.check()
    def qux():
        """qux"""

@check50.check()
def bar():
    """bar"""

@check50.check(foo)
def baz():
    """baz"""
