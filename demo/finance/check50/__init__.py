import check50
import check50.flask
from functools import wraps

APP_NAME = "application.py"

def register(app, username, password, confirmation):
    """Helper functoin for registering user"""
    form = {"username": username, "password": password, "confirmation": confirmation}
    return app.post("/register", data=form)

def login(app, username, password):
    """Helper function for logging in"""
    return app.post("/login", data={"username": username, "password": password})

def validate_form(app, route, fields, field_tag="input"):
    """Make sure HTML form at `route` has input fields given by `fields`"""
    if not isinstance(fields, list):
        fields = [fields]

    content = app.get(route).content()
    required = {field: False for field in fields}
    for tag in content.find_all(field_tag):
        try:
            name = tag.attrs["name"]
            if required[name]:
                raise Error("found more than one field called \"{}\"".format(name))
        except KeyError:
            pass
        else:
            log.append("found required \"{}\" field".format(name))
            required[name] = True

    try:
        missing = next(name for name, found in required.items() if not found)
    except StopIteration:
        pass
    else:
        raise Error("expected to find {} field with name \"{}\", but none found".format(field_tag, missing))

    if content.find("button", type="submit") is None:
        raise Error("expected button to submit form, but none was found")

def login(app, username, password):
    """Checks that user can log in"""
    return app.post("/login", data={"username": username, "password": password})

def quote(app, ticker):
    """Checks that getting a quote results in desired outcome"""
    return app.post("/quote", data={"symbol": ticker})

def transaction(app, route, symbol, shares):
    return app.post("{}".format(route), data={"symbol": symbol, "shares": shares})

@check50.check()
def exists():
    """application.py exists"""
    check50.require(APP_NAME)

@check50.check()
def startup():
    """application starts up"""
    check50.flask.app(APP_NAME).get("/").status(200)

@check50.check()
def register_page():
    """register page has all required elements"""
    app = check50.flask.app(APP_NAME)
    validate_form(app, "/register", ["username", "password", "confirmation"])

@check50.check()
def simple_register():
    """registering user succeeds"""
    app = check50.flask.app(APP_NAME)
    register(app, "cs50", "ohHai28!", "ohHai28!").status(200)

@check50.check()
def register_empty_field_fails():
    """registration with an empty field fails"""
    app = check50.flask.app(APP_NAME)
    for user in [("", "crimson", "crimson"), ("jharvard", "crimson", ""), ("jharvard", "", "")]:
        register(app, *user).status(400)

@check50.check()
def register_password_mismatch_fails():
    """registration with password mismatch fails"""
    app = check50.flask.app(APP_NAME)
    register(app, "check50user1", "thisiscs50", "crimson").status(400)

@check50.check()
def register_reject_duplicate_username():
    """registration rejects duplicate username"""
    app = check50.flask.app(APP_NAME)
    user = ["elfie", "Doggo28!", "Doggo28!"]
    register(app, *user).status(200)
    register(app, *user).status(400)

@check50.check()
def login_page():
    """login page has all required elements"""
    app = check50.flask.app(APP_NAME)
    validate_form(app, "/login", ["username", "password"])

@check50.check()
def can_login():
    """logging in as registered user succceeds"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!").status(200).get("/", follow_redirects=False).status(200)

@check50.check()
def quote_page():
    """quote page has all required elements"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    validate_form(app, "/quote", "symbol")

@check50.check()
def quote_handles_invalid():
    """quote handles invalid ticker symbol"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    quote(app, "ZZZ").status(400)

@check50.check()
def quote_handles_blank():
    """quote handles blank ticker symbol"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    quote(app, "").status(400)

@check50.check()
def quote_handles_valid():
    """quote handles valid ticker symbol"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    quote(app, "AAAA").status(200).content(r"28\.00", "28.00", name="body")

@check50.check()
def buy_page():
    """buy page has all required elements"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    validate_form(app, "/buy", ["shares", "symbol"])

@check50.check()
def buy_handles_invalid():
    """buy handles invalid ticker symbol"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    transaction(app, "/buy", "ZZZZ", "2").status(400)

@check50.check()
def buy_handles_incorrect_shares():
    """buy handles fractional, negative, and non-numeric shares"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    transaction(app, "/buy", "AAAA", "-1").status(400)
    transaction(app, "/buy", "AAAA", "1.5").status(400)
    transaction(app, "/buy", "AAAA", "foo").status(400)

@check50.check()
def buy_handles_valid():
    """buy handles valid purchase"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    transaction(app, "/buy", "AAAA", "4").content(r"112\.00", "112.00").content(r"9,?888\.00", "9,888.00")

@check50.check()
def sell_page():
    """sell page has all required elements"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    validate_form(app, "/sell", ["shares"])
    validate_form(app, "/sell", ["symbol"], field_tag="select")

@check50.check()
def sell_handles_invalid():
    """sell handles invalid number of shares"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    transaction(app, "/sell", "AAAA", "8").status(400)

@check50.check()
def sell_handles_valid():
    """sell handles valid sale"""
    app = check50.flask.app(APP_NAME)
    login(app, "cs50", "ohHai28!")
    transaction(app, "/sell", "AAAA", "2").content("56\.00", "56.00").content(r"9,?944\.00", "9,944.00")
