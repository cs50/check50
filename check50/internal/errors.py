from . import utils

class Error(Exception):
    """Class to wrap errors in students' checks."""

    def __init__(self, rationale=None, helpers=None, result="FAIL"):
        self.rationale = rationale
        self.helpers = helpers
        self.result = result

class InternalError(Exception):
    """Error during execution of check50."""

    def __init__(self, msg):
        self.msg = msg

class Mismatch:
    """Class which represents that expected output did not match actual output."""

    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual

    def __str__(self):
        return "expected {}, not {}".format(utils.raw(self.expected),
                                            utils.raw(self.actual))

    def __repr__(self):
        return "Mismatch(expected={}, actual={})".format(repr(self.expected), repr(self.actual))
