import check50

@check50.check()
@check50.hidden("foo")
def check():
    check50.log("AHHHHHHHHHHHHHHHHHHH")
    raise check50.Failure("AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
