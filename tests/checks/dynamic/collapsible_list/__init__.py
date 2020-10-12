import check50

@check50.check(dynamic=True)
def foo():
    """foo"""
    with open("answer.txt") as f:
        answer = f.read().strip()

    if answer != "correct":
        raise check50.Failure("")

    @check50.check()
    def bar():
        """bar"""

    @check50.check()
    def baz():
        """baz"""
