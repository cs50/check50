import check50
import check50.internal
import os

# First import happens in discovery
if not os.path.exists("data.txt"):
    check50.include("data.txt")

with open("data.txt", "a") as f:
    f.write("foo")

# Second import happens in static check "foo"
@check50.check()
def foo():
    """foo"""
    with open(check50.internal.run_root_dir / "data.txt") as f:
        content = f.read().strip()
        print(content)
        if content != "foofoo":
            raise check50.Failure(content)

# Dynamic checks don't re-import
@check50.check(dynamic=True)
def bar():
    """bar"""
    with open(check50.internal.run_root_dir / "data.txt") as f:
        content = f.read().strip()
        if content != "foofoo":
            raise check50.Failure(content)
