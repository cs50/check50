from pexpect.exceptions import EOF, TIMEOUT

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

class Mismatch(object):
    """Class which represents that expected output did not match actual output."""

    def __init__(self, expected, actual):
        self.expected = expected
        self.actual = actual

    def __str__(self):
        return "expected {}, not {}".format(self.raw(self.expected),
                                            self.raw(self.actual))

    def __repr__(self):
        return "Mismatch(expected={}, actual={})".format(repr(expected), repr(actual))

    @staticmethod
    def raw(s):
        """Get raw representation of s, truncating if too long"""

        if isinstance(s, list):
            s = "\n".join(s)

        if s == EOF:
            return "EOF"

        s = repr(s)  # get raw representation of string
        s = s[1:-1]  # strip away quotation marks
        if len(s) > 15:
            s = s[:15] + "..."  # truncate if too long
        return "\"{}\"".format(s)
