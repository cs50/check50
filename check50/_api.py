import hashlib
import functools
import numbers
import os
import re
import shlex
import shutil
import signal
import sys
import time

import pexpect
from pexpect.exceptions import EOF, TIMEOUT

from . import internal, regex

_log = []
internal.register.before_every(_log.clear)


def log(line):
    """
    Add to check log

    :param line: line to be added to the check log
    :type line: str

    The check log is student-visible via the ``--log`` flag to ``check50``.
    """
    _log.append(line.replace("\n", "\\n"))


_data = {}
internal.register.before_every(_data.clear)


def data(**kwargs):
    """
    Add data to the check payload

    :params kwargs: key/value mappings to be added to the check payload

    Example usage::

        check50.data(time=7.3, mem=23)

    """

    _data.update(kwargs)


def include(*paths):
    """
    Copy files/directories from the check directory (:data:`check50.internal.check_dir`),
    to the current directory

    :params paths: files/directories to be copied

    Example usage::

        check50.include("foo.txt", "bar.txt")
        assert os.path.exists("foo.txt") and os.path.exists("bar.txt")

    """
    cwd = os.getcwd()
    for path in paths:
        _copy((internal.check_dir / path).resolve(), cwd)


def hash(file):
    """
    Hashes file using SHA-256.

    :param file: name of file to be hashed
    :type file: str
    :rtype: str
    :raises check50.Failure: if ``file`` does not exist

    """

    exists(file)
    log(_("hashing {}...").format(file))

    # https://stackoverflow.com/a/22058673
    with open(file, "rb") as f:
        sha256 = hashlib.sha256()
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
        return sha256.hexdigest()


def exists(*paths):
    """
    Assert that all given paths exist.

    :params paths: files/directories to be checked for existence
    :raises check50.Failure: if any ``path in paths`` does not exist

    Example usage::

        check50.exists("foo.c", "foo.h")

    """
    for path in paths:
        log(_("checking that {} exists...").format(path))
        if not os.path.exists(path):
            raise Failure(_("{} not found").format(path))


def import_checks(path):
    """
    Import checks module given relative path.

    :param path: relative path from which to import checks module
    :type path: str
    :returns: the imported module
    :raises FileNotFoundError: if ``path / .check50.yaml`` does not exist
    :raises yaml.YAMLError: if ``path / .check50.yaml`` is not a valid YAML file

    This function is particularly useful when a set of checks logically extends
    another, as is often the case in CS50's own problems that have a "less comfy"
    and "more comfy" version. The "more comfy" version can include all of the
    "less comfy" checks like so::

        less = check50.import_checks("../less")
        from less import *

    .. note::
        the ``__name__`` of the imported module is given by the basename
        of the specified path (``less`` in the above example).

    """
    dir = internal.check_dir / path
    file = internal.load_config(dir)["checks"]
    mod = internal.import_file(dir.name, (dir / file).resolve())
    sys.modules[dir.name] = mod
    return mod



class run:
    """
    Run a command.

    :param command: command to be run
    :param env: environment in which to run command
    :type command: str
    :type env: dict

    By default, the command will be run using the same environment as ``check50``,
    these mappings may be overriden via the ``env`` parameter::

        check50.run("./foo").stdin("foo").stdout("bar").exit(0)
        check50.run("./foo", env={ "HOME": "/" }).stdin("foo").stdout("bar").exit(0)

    """

    def __init__(self, command, env={}):
        log(_("running {}...").format(command))

        full_env = os.environ.copy()
        full_env.update(env)

        # Workaround for OSX pexpect bug http://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits
        # Workaround from https://github.com/pexpect/pexpect/issues/373
        command = "bash -c {}".format(shlex.quote(command))
        self.process = pexpect.spawn(command, encoding="utf-8", echo=False, env=full_env)

    def stdin(self, line, str_line=None, prompt=True, timeout=3):
        """
        Send line to stdin, optionally expect a prompt.

        :param line: line to be send to stdin
        :type line: str
        :param str_line: what will be displayed as the delivered input, a human \
                           readable form of ``line``
        :type str_line: str
        :param prompt: boolean indicating whether a prompt is expected, if True absorbs \
                       all of stdout before inserting line into stdin and raises \
                       :class:`check50.Failure` if stdout is empty
        :type prompt: bool
        :param timeout: maximum number of seconds to wait for prompt
        :type timeout: int / float
        :raises check50.Failure: if ``prompt`` is set to True and no prompt is given

        """
        if str_line is None:
            str_line = line

        if line == EOF:
            log("sending EOF...")
        else:
            log(_("sending input {}...").format(str_line))

        if prompt:
            try:
                self.process.expect(".+", timeout=timeout)
            except (TIMEOUT, EOF):
                raise Failure(_("expected prompt for input, found none"))
            except UnicodeDecodeError:
                raise Failure(_("output not valid ASCII text"))

            # Consume everything on the output buffer
            try:
                for _i in range(int(timeout * 10)):
                    self.process.expect(".+", timeout=0.1)
            except (TIMEOUT, EOF):
                pass

        try:
            if line == EOF:
                self.process.sendeof()
            else:
                self.process.sendline(line)
        except OSError:
            pass
        return self

    def stdout(self, output=None, str_output=None, regex=True, timeout=3, show_timeout=False):
        """
        Retrieve all output from stdout until timeout (3 sec by default). If ``output``
        is None, ``stdout`` returns all of the stdout outputted by the process, else
        it returns ``self``.

        :param output: optional output to be expected from stdout, raises \
                       :class:`check50.Failure` if no match \
                       In case output is a float or int, the check50.number_regex \
                       is used to match just that number". \
                       In case output is a stream its contents are used via output.read().
        :type output: str, int, float, stream
        :param str_output: what will be displayed as expected output, a human \
                           readable form of ``output``
        :type str_output: str
        :param regex: flag indicating whether ``output`` should be treated as a regex
        :type regex: bool
        :param timeout: maximum number of seconds to wait for ``output``
        :type timeout: int / float
        :param show_timeout: flag indicating whether the timeout in seconds \
                                  should be displayed when a timeout occurs
        :type show_timeout: bool
        :raises check50.Mismatch: if ``output`` is specified and nothing that the \
                                  process outputs matches it
        :raises check50.Failure: if process times out or if it outputs invalid UTF-8 text.

        Example usage::

            check50.run("./hello").stdout("[Hh]ello, world!?", "hello, world").exit()

            output = check50.run("./hello").stdout()
            if not re.match("[Hh]ello, world!?", output):
                raise check50.Mismatch("hello, world", output)
        """
        if output is None:
            self._wait(timeout)
            return self.process.before.replace("\r\n", "\n").lstrip("\n")

        # In case output is a stream (file-like object), read from it
        try:
            output = output.read()
        except AttributeError:
            pass

        if str_output is None:
            str_output = str(output)

        # In case output is an int/float, use a regex to match exactly that int/float
        if isinstance(output, numbers.Number):
            regex = True
            output = globals()["regex"].decimal(output)

        expect = self.process.expect if regex else self.process.expect_exact

        if output == EOF:
            log(_("checking for EOF..."))
        else:
            output = str(output).replace("\n", "\r\n")
            log(_("checking for output \"{}\"...").format(str_output))

        try:
            expect(output, timeout=timeout)
        except EOF:
            result = self.process.before + self.process.buffer
            if self.process.after != EOF:
                result += self.process.after
            raise Mismatch(str_output, result.replace("\r\n", "\n"))
        except TIMEOUT:
            if show_timeout:
                raise Missing(str_output, self.process.before,
                              help=_("check50 waited {} seconds for the output of the program").format(timeout))
            raise Missing(str_output, self.process.before)
        except UnicodeDecodeError:
            raise Failure(_("output not valid ASCII text"))
        except Exception:
            raise Failure(_("check50 could not verify output"))

        # If we expected EOF and we still got output, report an error.
        if output == EOF and self.process.before:
            raise Mismatch(EOF, self.process.before.replace("\r\n", "\n"))

        return self

    def reject(self, timeout=1):
        """
        Check that the process survives for timeout. Useful for checking whether program is waiting on input.

        :param timeout: number of seconds to wait
        :type timeout: int / float
        :raises check50.Failure: if process ends before ``timeout``

        """
        log(_("checking that input was rejected..."))
        try:
            self._wait(timeout)
        except Failure as e:
            if not isinstance(e.__cause__, TIMEOUT):
                raise
        else:
            raise Failure(_("expected program to reject input, but it did not"))
        return self

    def exit(self, code=None, timeout=5):
        """
        Wait for process to exit or until timeout (5 sec by default) and asserts
        that process exits with ``code``. If ``code`` is ``None``, returns the code
        the process exited with.

        ..note:: In order to ensure that spawned child processes do not outlive the check that spawned them, it is good practice to call either method (with no arguments if the exit code doesn't matter) or ``.kill()`` on every spawned process.

        :param code: code to assert process exits with
        :type code: int
        :param timeout: maximum number of seconds to wait for the program to end
        :type timeout: int / float
        :raises check50.Failure: if ``code`` is given and does not match the actual exitcode within ``timeout``

        Example usage::

            check50.run("./hello").exit(0)

            code = check50.run("./hello").exit()
            if code != 0:
                raise check50.Failure(f"expected exit code 0, not {code}")


        """
        self._wait(timeout)

        if code is None:
            return self.exitcode

        log(_("checking that program exited with status {}...").format(code))
        if self.exitcode != code:
            raise Failure(_("expected exit code {}, not {}").format(code, self.exitcode))
        return self

    def kill(self):
        """Kill the process.

        Child will first be sent a ``SIGHUP``, followed by a ``SIGINT`` and
        finally a ``SIGKILL`` if it ignores the first two."""
        self.process.close(force=True)
        return self

    def _wait(self, timeout=5):
        try:
            self.process.expect(EOF, timeout=timeout)
        except TIMEOUT:
            raise Failure(_("timed out while waiting for program to exit")) from TIMEOUT(timeout)
        except UnicodeDecodeError:
            raise Failure(_("output not valid ASCII text"))

        self.kill()

        if self.process.signalstatus == signal.SIGSEGV:
            raise Failure(_("failed to execute program due to segmentation fault"))

        self.exitcode = self.process.exitstatus
        return self


class Failure(Exception):
    """
    Exception signifying check failure.

    :param rationale: message to be displayed capturing why the check failed
    :type rationale: str
    :param help: optional help message to be displayed
    :type help: str

    Example usage::

        out = check50.run("./cash").stdin("4.2").stdout()
        if 10 not in out:
            help = None
            if 11 in out:
                help = "did you forget to round your result?"
            raise check50.Failure("Expected a different result", help=help)
    """

    def __init__(self, rationale, help=None):
        self.payload = {"rationale": rationale, "help": help}

    def __str__(self):
        return self.payload["rationale"]


class Missing(Failure):
    """
    Exception signifying check failure due to an item missing from a collection.
    This is typically a specific substring in a longer string, for instance the contents of stdout.

    :param item: the expected item / substring
    :param collection: the collection / string
    :param help: optional help message to be displayed
    :type help: str

    Example usage::

        actual = check50.run("./fibonacci 5").stdout()

        if "5" not in actual and "3" in actual:
            help = "Be sure to start the sequence at 1"
            raise check50.Missing("5", actual, help=help)

    """

    def __init__(self, missing_item, collection, help=None):
        super().__init__(rationale=_("Did not find {} in {}").format(_raw(missing_item), _raw(collection)), help=help)

        if missing_item == EOF:
            missing_item = "EOF"

        self.payload.update({"missing_item": str(missing_item), "collection": str(collection)})


class Mismatch(Failure):
    """
    Exception signifying check failure due to a mismatch in expected and actual outputs.

    :param expected: the expected value
    :param actual: the actual value
    :param help: optional help message to be displayed
    :type help: str

    Example usage::

        from re import match
        expected = "[Hh]ello, world!?\\n"
        actual = check50.run("./hello").stdout()
        if not match(expected, actual):
            help = None
            if match(expected[:-1], actual):
                help = r"did you forget a newline ('\\n') at the end of your printf string?"
            raise check50.Mismatch("hello, world\\n", actual, help=help)

    """

    def __init__(self, expected, actual, help=None):
        super().__init__(rationale=_("expected {}, not {}").format(_raw(expected), _raw(actual)), help=help)

        if expected == EOF:
            expected = "EOF"

        if actual == EOF:
            actual = "EOF"

        self.payload.update({"expected": expected, "actual": actual})


def hidden(failure_rationale):
    """
    Decorator that marks a check as a 'hidden' check. This will suppress the log
    accumulated throughout the check and will catch any :class:`check50.Failure`s thrown
    during the check, and reraising a new :class:`check50.Failure` with the given ``failure_rationale``.

    :param failure_rationale: the rationale that will be displayed to the student if the check fails
    :type failure_rationale: str

    Exaple usage::

        @check50.check()
        @check50.hidden("Your program isn't returning the expected result. Try running it on some sample inputs.")
        def hidden_check():
            check50.run("./foo").stdin("bar").stdout("baz").exit()

    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Failure:
                raise Failure(failure_rationale)
            finally:
                _log.clear()
        return wrapper
    return decorator


def _raw(s):
    """Get raw representation of s, truncating if too long."""

    if isinstance(s, list):
        s = "\n".join(_raw(item) for item in s)

    if s == EOF:
        return "EOF"

    s = f'"{repr(str(s))[1:-1]}"'
    if len(s) > 15:
        s = s[:15] + "...\""  # Truncate if too long
    return s


def _copy(src, dst):
    """Copy src to dst, copying recursively if src is a directory."""
    try:
        shutil.copy(src, dst)
    except IsADirectoryError:
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.copytree(src, dst)
