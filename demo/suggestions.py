import re

from check50 import *

# Notes:
# spawn should not be in check class < it doesn't check!
# Break check50.py up, there's too little cohesion, for example:
    # valgrind should not be mentioned in spawn nor in check50.py move it to valgrind50.py < it's not essential
    # (Flask)app should not be in check class nor in check50.py move it to flask50.py< it's not essential

class Hello(Checks):

    @check()
    def exists():
        """hello.c exists."""
        require("hello.py")

    """
    Stick to the framework v1
    Pros:
    * easily compilable from a txt-based format
    * explicit
    * no Python experience required
    Cons:
    * there's always missing features
    * on() behaviour takes some getting used to, only part of framework that you cannot chain and get the same outcome
    """
    @check("exists")
    def prints_hello():
        """prints "hello, world\\n" """
        expected = "[Hh]ello, world!?\n"
        check = spawn("python3 hello.py").stdout().match(expected)
        check.on(fail).match(expected[-1]).help("Did you forget a newline (\"\\n\") at the end of your printf string?")
        check.on(fail).match(expected.replace(",", "")).help("Did you forget the ,?")

    """
    Stick to the framework v2
    Pros:
    * easily compilable from a txt-based format
    * explicit
    * no Python experience required
    * can chain all you want
    Cons:
    * there's always missing features, and extending requires Python + Framework knowledge
    """
    @check("exists")
    def prints_hello():
        expected = "[Hh]ello, world!?\n"
        spawn("python3 hello.py")
            .stdout()
            .match(expected)
            .iff(has_failed)
                .match(expected[-1])
                .help("Did you forget a newline (\"\\n\") at the end of your printf string?")
            .endiff()
            .iff(has_failed)
                .match(expected.replace(",", ""))
                .help("Did you forget the ,?")
            .endiff()

    """
    Expose internal api
    Pros:
    * explicit
    * forces a good programming style in check50 (eat your own dogfood)
    * makes extension simpler, only need knowledge of Python + internal API:
        def atleast_one_match(check, col, regex)
            if not any(match(item, regex) for item in col):
                check.fail("no matches found!")
    Cons:
    * hard to compile from txt-based format
    * mix of styles, chaining methods vs sequentially calling functions
    """
    @check("exists")
    def prints_hello():
        """prints "hello, world\\n" """
        expected = "[Hh]ello, world!?\n"

        check = spawn("python3 hello.py").stdout().match(expected)

        if has_failed(check):
            if match(check.stdout.last, expected[-1]):
                helper("Did you forget a newline (\"\\n\") at the end of your printf string?")
            if match(check.stdout.last, expected.replace(",", "")):
                helper("Did you forget the ,?")
