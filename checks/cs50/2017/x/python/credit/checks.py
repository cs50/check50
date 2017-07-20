import os
import sys

sys.path.append(os.getcwd())
from check50 import *

class CreditPython(TestCase):

    @check()
    def exists(self):
        """credit.py exists."""
        super(CreditPython, self).exists("credit.py")

    @check("exists")
    def AMEX(self):
        """identifies 378282246310005 as AMEX"""
        self.spawn("python3 credit.py").stdin("378282246310005").stdout("^AMEX\n$", "AMEX").exit(0)

    @check("exists")
    def AMEX2(self):
        """identifies 371449635398431 as AMEX"""
        self.spawn("python3 credit.py").stdin("371449635398431").stdout("^AMEX\n$", "AMEX").exit(0)

    @check("exists")
    def MASTERCARD(self):
        """identifies 5555555555554444 as MASTERCARD"""
        self.spawn("python3 credit.py").stdin("5555555555554444").stdout("^MASTERCARD\n$", "MASTERCARD").exit(0)

    @check("exists")
    def MASTERCARD2(self):
        """identifies 5105105105105100 as MASTERCARD"""
        self.spawn("python3 credit.py").stdin("5105105105105100").stdout("^MASTERCARD\n$", "MASTERCARD").exit(0)

    @check("exists")
    def VISA(self):
        """identifies 4111111111111111 as VISA"""
        self.spawn("python3 credit.py").stdin("4111111111111111").stdout("^VISA\n$", "VISA").exit(0)

    @check("exists")
    def VISA2(self):
        """identifies 4012888888881881 as VISA"""
        self.spawn("python3 credit.py").stdin("4012888888881881").stdout("^VISA\n$", "VISA").exit(0)

    @check("exists")
    def INVALID(self):
        """identifies 1234567890 as INVALID"""
        self.spawn("python3 credit.py").stdin("1234567890").stdout("^INVALID\n$", "INVALID").exit(0)

    @check("exists")
    def reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.spawn("python3 credit.py").stdin("foo").reject()

    @check("exists")
    def reject_empty(self):
        """rejects a non-numeric input of "" """
        self.spawn("python3 credit.py").stdin("").reject()
