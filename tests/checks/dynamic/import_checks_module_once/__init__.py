import check50
import os

if not os.path.exists("data.txt"):
    check50.include("data.txt")

with open("data.txt") as f:
    assert f.read().strip() == "foo"

with open("data.txt", "w"):
    pass

@check50.check(dynamic=True)
def foo():
    """foo"""

@check50.check(dynamic=True)
def bar():
    """bar"""
