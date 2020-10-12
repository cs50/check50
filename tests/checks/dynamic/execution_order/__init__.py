import check50
import check50.internal
import os

FILE_PATH = check50.internal.run_root_dir / "data.txt"

if not os.path.exists(FILE_PATH):
    with open(FILE_PATH, "w") as f:
        pass

# first (statically) defined dynamic check second
@check50.check(dynamic=True)
def foo():
    """foo"""
    with open(FILE_PATH, "a") as f:
        f.write("2")

    # first dynamically created dynamic check fourth
    @check50.check()
    def qux():
        """qux"""
        with open(FILE_PATH, "a") as f:
            f.write("4")

# static check goes first
@check50.check()
def bar():
    """bar"""
    with open(FILE_PATH, "a") as f:
        f.write("1")

# second (statically) defined dynamic check third
@check50.check(foo)
def baz():
    """baz"""
    with open(FILE_PATH, "a") as f:
        f.write("3")

    # last dynamically created dynamic check fifth
    @check50.check()
    def quux():
        """quux"""
        with open(FILE_PATH) as f:
            raise check50.Failure(f.read())
