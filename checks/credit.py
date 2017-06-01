import os
import sys

sys.path.append(os.getcwd())
from check50 import Test, check

class Credit(Test):
    
    @check()
    def exists(self):
        """credit.c exists."""
        self.check_exists("credit.c")
    
    @check("exists")
    def compiles(self):
        """credit.c compiles."""
        self.check_compiles("clang -o credit credit.c -lcs50")
    
    @check("exists", "compiles")
    def test1(self):
        """identifies 378282246310005 as AMEX"""
        self.check_output("./credit", "378282246310005", "AMEX\n")

    @check("exists", "compiles")
    def test2(self):
        """identifies 371449635398431 as AMEX"""
        self.check_output("./credit", "371449635398431", "AMEX\n")

    @check("exists", "compiles")
    def test3(self):
        """identifies 5555555555554444 as MASTERCARD"""
        self.check_output("./credit", "5555555555554444", "MASTERCARD\n")

    @check("exists", "compiles")
    def test4(self):
        """identifies 5105105105105100 as MASTERCARD"""
        self.check_output("./credit", "5105105105105100", "MASTERCARD\n")

    @check("exists", "compiles")
    def test5(self):
        """identifies 4111111111111111 as VISA"""
        self.check_output("./credit", "4111111111111111", "VISA\n")

    @check("exists", "compiles")
    def test6(self):
        """identifies 4012888888881881 as VISA"""
        self.check_output("./credit", "4012888888881881", "VISA\n")

    @check("exists", "compiles")
    def test7(self):
        """identifies 1234567890 as INVALID"""
        self.check_output("./credit", "1234567890", "INVALID\n")

    @check("exists", "compiles")
    def test_reject_foo(self):
        """rejects a non-numeric input of "foo" """
        self.check_reject("./credit", "foo")

    @check("exists", "compiles")
    def test_reject_empty(self):
        """rejects a non-numeric input of "" """
        self.check_reject("./credit", "")

test_cases = Test.test_cases
remove = ["credit"]
