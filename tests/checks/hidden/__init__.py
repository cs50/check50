import check50

@check50.check(hidden=True)
def check():
    check50.log("AHHHHHHHHHHHHHHHHHHH")
    raise check50.Failure("AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
