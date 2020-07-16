import check50

@check50.check(dynamic=True)
def foo():
    """foo"""

    def bar():
        """bar"""
        pass

    check50.check()(bar)
    check50.check()(bar)
