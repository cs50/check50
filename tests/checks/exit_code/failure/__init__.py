import check50

@check50.check()
def should_fail():
    raise check50.Failure("BANG!")
