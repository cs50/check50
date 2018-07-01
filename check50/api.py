from contextlib import contextmanager
import hashlib
import os
import shutil
import signal
import sys
import time
import importlib

import shlex
import pexpect
from pexpect.exceptions import EOF, TIMEOUT

from . import internal


_log = []
internal.register.before_every(_log.clear)


def log(line):
    """Add to check log

    :param line: line to be added to the check log
    :type line: str

    The check log is student-visible via the ``--log`` flag to ``check50``.
    """
    _log.append(line)


_data = {}
internal.register.before_every(_data.clear)


def data(**kwargs):
    """Add data to the check payload

    :params kwargs: key/value mappings to be added to the check payload

    Example usage::

        check50.data(time=7.3, mem=23)
    """

    _data.update(kwargs)


def include(*paths):
    """Copy files/directories from the check directory (:data:`check50.internal.check_dir`), to the current directory

    :params paths: files/directories to be copied


    Example usage::

        check50.include("foo.txt", "bar.txt")
        assert os.path.exists("foo.txt") and os.path.exists("bar.txt")

    """
    cwd = os.getcwd()
    for path in paths:
        _copy((internal.check_dir / path).resolve(), cwd)


def hash(file):
    """Hashes file using SHA-256.

    :param file: name of file to be hashed
    :type file: str
    :rtype: str
    :raises check50.Failure: if ``file`` does not exist

    """

    exists(file)
    log(f"Hashing {file}...")

    # https://stackoverflow.com/a/22058673
    with open(file, "rb") as f:
        sha256 = hashlib.sha256()
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
        return sha256.hexdigest()


def exists(*paths):
    """Assert that all given paths exist.

    :params paths: files/directories to be checked for existence
    :raises check50.Failure: if any ``path in paths`` does not exist

    Example usage::

        check50.exists("foo.c", "foo.h")
    """
    for path in paths:
        log(f"Checking that {path} exists...")
        if not os.path.exists(path):
            raise Failure(f"{path} not found")


def import_checks(path):
    """ Import checks module given relative path.

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
        The ``__name__`` of the imported module is given by the basename
        of the specified path (``less`` in the above example).
    """
    dir = internal.check_dir / path
    name = dir.name

    file = internal.parse_config(dir)["checks"]
    mod = internal.import_file(name, (dir / file).resolve())
    sys.modules[name] = mod
    return mod


class run:
    """Run a command.

    :param command: command to be run
    :param env: environment in which to run command
    :type command: str
    :type env: dict

    By default, the command will be run using the same environment as ``check50``, these mappings may be overriden via the ``env`` parameter::

        check50.run("./foo").stdin("foo").stdout("bar").exit(0)
        check50.run("./foo", env={ "HOME": "/" }).stdin("foo").stdout("bar").exit(0)

    """

    def __init__(self, command, env={}):
        log(f"running {command}...")

        full_env = os.environ.copy()
        full_env.update(env)

        # Workaround for OSX pexpect bug http://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits
        # Workaround from https://github.com/pexpect/pexpect/issues/373
        command = "bash -c {}".format(shlex.quote(command))
        self.process = pexpect.spawn(command, encoding="utf-8", echo=False, env=full_env)


    def stdin(self, line, prompt=True, timeout=3):
        """Send a line to the stdin of the spawned process.

        :param line: line to be sent to the process
        :type line: str
        :param prompt: indicates whether we should expect that the child process to have printed a prompt
        :type prompt: bool
        :param timeout: number of seconds we should wait for child process to print prompt
        :type timeout: int
        """
        if line == EOF:
            log("sending EOF...")
        else:
            log(f"sending input {line}...")

        if prompt:
            try:
                self.process.expect(".+", timeout=timeout)
            except (TIMEOUT, EOF):
                raise Failure("expected prompt for input, found none")
        try:
            if line == EOF:
                self.process.sendeof()
            else:
                self.process.sendline(line)
        except OSError:
            pass
        return self

    def stdout(self, output=None, str_output=None, regex=True, timeout=3):
        """
        Retrieve all output from stdout until timeout (3 sec by default)
        If output (str / File obj) is given, matches stdout until output is matched, or raises Mismatch
        If str_output is given, use str_output (human readable form of output) in Mismatch if raised
        If regex is set to False (True by default) perform an exact match otherwise match with regex
        """
        if output is None:
            return self._wait(timeout)._output

        try:
            output = output.read()
        except AttributeError:
            pass

        expect = self.process.expect if regex else self.process.expect_exact

        if str_output is None:
            str_output = output

        if output == EOF:
            log("checking for EOF...")
        else:
            output = output.replace("\n", "\r\n")
            log(f"checking for output \"{str_output}\"...")

        try:
            expect(output, timeout=timeout)
        except EOF:
            result = self.process.before + self.process.buffer
            if self.process.after != EOF:
                result += self.process.after
            raise Mismatch(str_output, result.replace("\r\n", "\n"))
        except TIMEOUT:
            raise Failure(f"did not find {_raw(str_output)}")
        except UnicodeDecodeError:
            raise Failure("output not valid ASCII text")
        except Exception:
            raise Failure("check50 could not verify output")

        # If we expected EOF and we still got output, report an error.
        if output == EOF and self.process.before:
            raise Mismatch(EOF, self.process.before.replace("\r\n", "\n"))

        return self

    def reject(self, timeout=1):
        """
        Check that the process survives for timeout (1 second by default)
        Usecase: check that program rejected input and is now waiting on new input
        """
        log("checking that input was rejected...")
        try:
            self._wait(timeout)
        except Failure as e:
            if not isinstance(e.__cause__, TIMEOUT):
                raise
        else:
            raise Failure("expected program to reject input, but it did not")
        return self

    def exit(self, code=None, timeout=5):
        """
        Wait for eof or until timeout (5 sec by default), returns the exitcode
        If code is given, matches exitcode vs code and raises Failure incase of mismatch
        """
        self._wait(timeout)

        if code is None:
            return self.exitcode

        log(f"checking that program exited with status {code}...")
        if self.exitcode != code:
            raise Failure(f"expected exit code {code}, not {self.exitcode}")
        return self

    def kill(self):
        """Kill the process"""
        self.process.close(force=True)
        return self

    def _wait(self, timeout=5):
        out = []
        end = time.time() + timeout
        while time.time() <= end:
            if not self.process.isalive():
                break
            try:
                bytes = self.process.read_nonblocking(size=1024, timeout=0)
            except TIMEOUT:
                pass
            except EOF:
                break
            except UnicodeDecodeError:
                raise Failure("output not valid ASCII text")
            else:
                out.append(bytes)
        else:
            raise Failure("timed out while waiting for program to exit") from TIMEOUT(timeout)

        # Read any remaining data in pipe.
        while True:
            try:
                bytes = self.process.read_nonblocking(size=1024, timeout=0)
            except (TIMEOUT, EOF):
                break
            else:
                out.append(bytes)

        self._output = "".join(out).replace("\r\n", "\n").lstrip("\n")
        self.kill()

        if self.process.signalstatus == signal.SIGSEGV:
            raise Failure("failed to execute program due to segmentation fault")

        self.exitcode = self.process.exitstatus
        return self


class Failure(Exception):
    def __init__(self, rationale, help=None):
        self.rationale = rationale
        self.help = help

    def __str__(self):
        return self.rationale

    def asdict(self):
        return {"rationale": self.rationale, "help": self.help}


class Mismatch(Failure):
    def __init__(self, expected, actual, help=None):
        super().__init__(rationale=f"expected {_raw(expected)}, not {_raw(actual)}", help=help)
        self.expected = expected
        self.actual = actual

    def asdict(self):
        return dict(expected=self.expected,
                    actual=self.actual,
                    **super().asdict())


def _raw(s):
    """Get raw representation of s, truncating if too long"""

    if isinstance(s, list):
        s = "\n".join(_raw(item) for item in s)

    if s == EOF:
        return "EOF"

    s = repr(s)  # get raw representation of string
    s = s[1:-1]  # strip away quotation marks
    if len(s) > 15:
        s = s[:15] + "..."  # truncate if too long
    return "\"{}\"".format(s)


def _copy(src, dst):
    """Copy src to dst, copying recursively if src is a directory."""
    try:
        shutil.copy(src, dst)
    except IsADirectoryError:
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.copytree(src, dst)
