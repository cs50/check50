import check50
import sys

# Set the excepthook to an unpicklable value, the run_check process will try to copy this
sys.excepthook = lambda type, value, traceback: "bar"

@check50.check()
def foo():
    """foo"""