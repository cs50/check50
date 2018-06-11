import re
import os
import sys
import imp
import errno
import urllib.parse as url

from bs4 import BeautifulSoup

from .api import log


def app(file):
    return App(file)


class App:
    def __init__(self, path):
        dir, file = os.path.split(path)
        name, _ = os.path.splitext(file)

        # add directory of flask app to sys.path so we can import it properly
        prevpath = sys.path[0]
        try:
            sys.path[0] = os.path.abspath(dir or ".")
            mod = imp.load_source(name, file)
        except FileNotFoundError:
            raise Fail("could not find {}".format(file))
        finally:
            # restore sys.path
            sys.path[0] = prevpath

        try:
            app = mod.app
        except AttributeError:
            raise Fail("{} does not contain an app".format(file))

        # initialize flask client
        app.testing = True
        self.client = app.test_client()

        self.response = None

    def get(self, route, data=None, params=None, follow_redirects=True):
        """Send GET request to `route`."""
        return self._send("GET", route, data, params, follow_redirects=follow_redirects)

    def post(self, route, data=None, params=None, follow_redirects=True):
        """Send POST request to `route`."""
        return self._send("POST", route, data, params, follow_redirects=follow_redirects)

    def status(self, code=None):
        """Throw error if http status code doesn't equal `code`or return the status code if `code is None."""
        if code is None:
            return self.response.status_code

        log(f"checking that status code {code} is returned...")
        if code != self.response.status_code:
            raise Fail("expected status code {}, but got {}".format(
                code, self.response.status_code))
        return self

    def raw_content(self, output=None, str_output=None):
        """Searches for `output` regex match within content of page, regardless of mimetype."""
        return self._search_page(output, str_output, self.response.data, lambda regex, content: regex.search(content.decode()))

    def content(self, output=None, str_output=None, **kwargs):
        """Searches for `output` regex within HTML page. kwargs are passed to BeautifulSoup's find function to filter for tags."""
        if self.response.mimetype != "text/html":
            raise Fail("expected request to return HTML, but it returned {}".format(
                self.response.mimetype))

        return self._search_page(
            output,
            str_output,
            BeautifulSoup(self.response.data, "html.parser"),
            lambda regex, content, **kwargs: any(regex.search(str(tag)) for tag in content.find_all(**kwargs)))

    def _send(self, method, route, data, params, **kwargs):
        """Send request of type `method` to `route`"""
        route = self._fmt_route(route, params)
        log(f"sending {method.upper()} request to {route}")

        try:
            self.response = getattr(self.client, method.lower())(route, data=data, **kwargs)
        except BaseException as e:  # Catch all exceptions thrown by app
            # TODO: Change Finance starter code for edX and remove this as well as app.testing = True in __init__
            log(f"exception raised in application: {type(e).__name__}: {e}")
            raise Fail("application raised an exception (see log for details)")

        return self

    def _search_page(self, output, str_output, content, match_fn, **kwargs):
        if output is None:
            return content

        if str_output is None:
            str_output = output

        log(f"checking that \"{str_output}\" is in page")
        regex = re.compile(output)

        if not match_fn(regex, content, **kwargs):
            raise Fail(f"expected to find \"{str_output}\" in page, but it wasn't found")

        return self

    @staticmethod
    def _fmt_route(route, params):
        parsed = url.urlparse(route)

        # convert params dict into urlencoded string
        params = url.urlencode(params) if params else ""

        # concatenate params
        param_str = "&".join((ps for ps in [params, parsed.query] if ps))
        if param_str:
            param_str = "?" + param_str

        # only display netloc if it isn't localhost
        return "".join([parsed.netloc if parsed.netloc != "localhost" else "", parsed.path, param_str])
