import check50

@check50.check(dynamic=True)
def foo():
    """foo"""

    def bar():
        """bar"""

    def baz():
        """baz"""

    check50.check(dependency=baz)(bar)
    check50.check(dependency=bar)(baz)
