import check50

@check50.check(dynamic=True)
def foo():
    """foo"""
    
    @check50.check()
    def bar():
        """bar"""
        pass
