import check50

@check50.check(dynamic=True)
def foo():
    """foo"""
    with open("answer.txt") as f:
        answer = f.read().strip()

    if answer != "correct":
        @check50.check()
        def bar():
            """bar"""

        @check50.check()
        def baz():
            """baz"""

        raise check50.Failure("")
