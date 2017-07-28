import os
import re
import requests
import sys

sys.path.append(os.getcwd())
from check50 import *
from selenium import webdriver

class Finance(Checks):

    BASE_PATH = "http://127.0.0.1:5000"
    
    def server_up(self):
        env = {
            "FLASK_APP": "application.py"
        }

        self.server = self.spawn("flask run", env=env)
        self.driver = webdriver.PhantomJS()

    def server_down(self):
        self.driver.close()
        self.server.kill()

    def override_lookup(self):
        """Replaces student's lookup function with a deterministic one."""
        self.append_code("helpers.py", File("lookup.py"))
    
    def register(self, username, password, confirmation, outcome):
        """Checks that registering results in success or failure."""

        # go to register page
        self.driver.get("{}/register".format(Finance.BASE_PATH))
        fields = self.driver.find_elements_by_tag_name("input")
    
        # check for input fields
        if len(fields) == 0:
            raise Error("No available input fields to register.")
        
        # fill in name, password, confiramtion
        fields_filled = 0
        for field in fields:
            name = field.get_attribute("name")
            if name == "username":
                fields_filled += 1
                field.send_keys(username)
            elif name == "password":
                fields_filled += 1
                field.send_keys(password)
            elif name == "confirmation":
                fields_filled += 1
                field.send_keys(confirmation)
        if fields_filled != 3:
            raise Error("Could not fill in username and/or password.")
    
        # search for register button
        buttons = self.driver.find_elements_by_tag_name("button")
        register_button = None
        for button in buttons:
            if button.text == "Register":
                register_button = button
        if register_button == None:
            raise Error("Could not find register button.")
        register_button.click()

        if "Apology" in self.driver.title and outcome:
            raise Error("Expected registration success, not rejection.")
        elif "Apology" not in self.driver.title and not outcome:
            raise Error("Expected registration rejection, not acceptance.")

    def login(self, username, password):
        """Checks that user can log in."""

        # go to login page
        self.driver.get("{}/login".format(Finance.BASE_PATH))
        fields = self.driver.find_elements_by_tag_name("input")
        fields_filled = 0
        for field in fields:
            name = field.get_attribute("name")
            if name == "username":
                fields_filled += 1
                field.send_keys(username)
            elif name == "password":
                fields_filled += 1
                field.send_keys(password)
        if fields_filled != 2:
            raise Error("Could not fill in username and/or password.")

        # search for log in button
        buttons = self.driver.find_elements_by_tag_name("button")
        login_button = None
        for button in buttons:
            if button.text == "Log In":
                login_button = button
        if login_button == None:
            raise Error("Could not find log in button.")
        login_button.click()

        if "Apology" in self.driver.title:
            raise Error("Expected login to succeed, not fail.")

    def quote(self, ticker, outcome, value=None):
        """Checks that getting a quote results in desired outcome."""

        # go to quote page
        self.driver.get("{}/quote".format(Finance.BASE_PATH))
        fields = self.driver.find_elements_by_tag_name("input")
    
        # find field to input quote
        quote_field = None
        for field in fields:
            name = field.get_attribute("name")
            if name == "symbol":
                quote_field = field
        if quote_field == None:
            raise Error("Could not input quote.")
        quote_field.send_keys(ticker)

        # search for quote button
        buttons = self.driver.find_elements_by_tag_name("button")
        quote_button = None
        for button in buttons:
            if button.text == "Quote":
                quote_button = button
        if quote_button == None:
            raise Error("Could not find quote button.")
        quote_button.click()

        if "Apology" in self.driver.title and outcome:
            raise Error("Expected quote success, not failure.")
        elif "Apology" not in self.driver.title and not outcome:
            raise Error("Expected quote failure, not success.")
        elif outcome and value:
            # check the output against the given value
            if str(value) not in self.driver.find_element_by_tag_name("body").text:
                raise Error("Expected quote not found.")

    def transaction(self, transaction, symbol, shares, outcome, value=None, remaining=None):
        """Checks that purchasing shares results in given outcome."""

        # go to buy page
        self.driver.get("{}/{}".format(Finance.BASE_PATH, transaction))
        fields = self.driver.find_elements_by_tag_name("input")

        # fill in fields
        fields_filled = 0
        for field in fields:
            name = field.get_attribute("name")
            if name == "symbol":
                fields_filled += 1
                field.send_keys(symbol)
            elif name == "shares":
                fields_filled += 1
                field.send_keys(shares)
        if fields_filled != 2:
            raise Error("Could not fill in symbol and/or shares.")

        # search for buy button
        buttons = self.driver.find_elements_by_tag_name("button")
        buy_button = None
        for button in buttons:
            if button.text == transaction.capitalize():
                buy_button = button
        if buy_button == None:
            raise Error("Could not find {} button.".format(transaction))
        buy_button.click()

        if "Apology" in self.driver.title and outcome:
            raise Error("Expected {} success, not failure.".format(transaction))
        elif "Apology" not in self.driver.title and not outcome:
            raise Error("Expected {} failure, not success.".format(transaction))

        # go to index and check balance
        if outcome and (value or remaining):
            self.driver.get(Finance.BASE_PATH)
            if value and not re.search(value, self.driver.page_source):
                raise Error("Expected to see value {}.".format(value))
            if remaining and not re.search(remaining, self.driver.page_source):
                raise Error("Expected to see cash of value {}.".format(remaining))


    @check()
    def exists(self):
        """application.py exists."""
        super().exists("application.py")

    @check("exists")
    def startup(self):
        """application starts up."""
        self.override_lookup()
        self.server_up()
        res = requests.get(Finance.BASE_PATH)
        if res.status_code != 200:
            raise Error((res.status_code, 200))
        self.server_down()

    @check("startup")
    def can_register(self):
        """user can register for account."""
        self.server_up()
        self.register("check50user1", "crimson", "crimson", True)
        self.server_down()

    @check("startup")
    def register_empty_field_fails(self):
        """registration with an empty field fails."""
        self.server_up()
        self.register("", "crimson", "crimson", False)
        self.register("check50user1", "", "crimson", False)
        self.register("check50user1", "", "", False)
        self.server_down()

    @check("startup")
    def register_password_mismatch_fails(self):
        """registration with password mismatch fails."""
        self.server_up()
        self.register("check50user1", "thisiscs50", "crimson", False)
        self.server_down()

    @check("startup")
    def register_reject_duplicate_username(self):
        """registration rejects duplicate username."""
        self.server_up()
        self.register("check50user1", "crimson", "crimson", True)
        self.register("check50user1", "crimson", "crimson", False)
        self.server_down()

    @check("can_register")
    def quote_handles_invalid(self):
        """quote handles invalid ticker symbol."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.quote("ZZZZ", False)
        self.server_down()

    @check("can_register")
    def quote_handles_blank(self):
        """quote handles blank ticker symbol."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.quote("", False)
        self.server_down()

    @check("can_register")
    def quote_handles_valid(self):
        """quote handles valid ticker symbol."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.quote("AAAA", True, value="28.00")
        self.server_down()

    @check("can_register")
    def buy_handles_invalid(self):
        """buy handles invalid ticker symbol."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.transaction("buy", "ZZZZ", "2", False)
        self.server_down()

    @check("can_register")
    def buy_handles_incorrect_shares(self):
        """buy handles fractional, negative, and non-numeric shares."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.transaction("buy", "AAAA", "-1", False)
        self.transaction("buy", "AAAA", "1.5", False)
        self.transaction("buy", "AAAA", "foo", False)
        self.server_down()

    @check("can_register")
    def buy_handles_valid(self):
        """buy handles valid purchase."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.transaction("buy", "AAAA", "4", True, value="112.00", remaining="9,?888.00")
        self.server_down()

    @check("buy_handles_valid")
    def sell_handles_invalid(self):
        """sell handles invalid ticker symbol."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.transaction("sell", "ZZZZ", "2", False)
        self.server_down()

    @check("buy_handles_valid")
    def sell_handles_valid(self):
        """sell handles valid sell."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.transaction("sell", "AAAA", "2", True, value="56.00", remaining="9,?944.00")
        self.server_down()

    @check("sell_handles_valid")
    def history(self):
        """history shows transactions."""
        self.server_up()
        self.login("check50user1", "crimson")
        self.transaction("buy", "BBBB", "1", True)
        self.driver.get("{}/history".format(Finance.BASE_PATH))
        if not re.search("14.00", self.driver.page_source):
            raise Error("Expected to see result of purchase in history.")
        if not re.search("28.00", self.driver.page_source):
            raise Error("Expected to see result of sale in history.")
