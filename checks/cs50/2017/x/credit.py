from check50 import *

@checks
class Credit(Checks):

    @check()
    def exists(self):
        """credit.c exists."""
        self.require("credit.c")

    @check("exists")
    def compiles(self):
        """credit.c compiles."""
        self.spawn("clang -o credit credit.c -lcs50 -lm").exit(0)

    @check("compiles")
    def test1(self):
        """identifies 378282246310005 as AMEX"""
        self.spawn("./credit").stdin("378282246310005").stdout("^AMEX\n", "AMEX\n").exit(0)

    @check("compiles")
    def test2(self):
        """identifies 371449635398431 as AMEX"""
        self.spawn("./credit").stdin("371449635398431").stdout("^AMEX\n", "AMEX\n").exit(0)

    @check("compiles")
    def test3(self):
        """identifies 5555555555554444 as MASTERCARD"""
        self.spawn("./credit").stdin("5555555555554444").stdout("^MASTERCARD\n", "MASTERCARD\n").exit(0)

    @check("compiles")
    def test4(self):
        """identifies 5105105105105100 as MASTERCARD"""
        self.spawn("./credit").stdin("5105105105105100").stdout("^MASTERCARD\n", "MASTERCARD\n").exit(0)

    @check("compiles")
    def test5(self):
        """identifies 4111111111111111 as VISA"""
        self.spawn("./credit").stdin("4111111111111111").stdout("^VISA\n", "VISA\n").exit(0)

    @check("compiles")
    def test6(self):
        """identifies 4012888888881881 as VISA"""
        self.spawn("./credit").stdin("4012888888881881").stdout("^VISA\n", "VISA\n").exit(0)

    @check("compiles")
    def test7(self):
        """identifies 1234567890 as INVALID"""
        self.spawn("./credit").stdin("1234567890").stdout("^INVALID\n", "INVALID\n").exit(0)

    @check("compiles")
    def test_reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.spawn("./credit").stdin("foo").reject()

    @check("compiles")
    def test_reject_empty(self):
        """rejects a non-numeric input of "" """
        self.spawn("./credit").stdin("").reject()

