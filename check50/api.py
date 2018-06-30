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


def run(command, env=None):
    """Runs a command in the specified environment.
    Returns a Process object representing the spawned child process"""
    log(f"running {command}...")

    if env is None:
        env = {}

    full_env = os.environ.copy()
    full_env.update(env)

    # Workaround for OSX pexpect bug http://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits
    # Workaround from https://github.com/pexpect/pexpect/issues/373
    command = "bash -c {}".format(shlex.quote(command))
    child = pexpect.spawn(command, encoding="utf-8", echo=False, env=full_env)

    return Process(child)


_log = []
internal.register.before_every(_log.clear)


def log(line):
    """Add line to check log."""
    _log.append(line)


_data = {}
internal.register.before_every(_data.clear)


def data(**kwargs):
    _data.update(kwargs)


def include(*paths):
    """Copies all given files from the check directory to the current directory."""
    cwd = os.getcwd()
    for path in paths:
        _copy((internal.check_dir / path).resolve(), cwd)


def hash(file):
    """Hashes file using SHA-256."""

    exists(file)
    log(f"Hashing {file}...")

    # https://stackoverflow.com/a/22058673
    with open(file, "rb") as f:
        sha256 = hashlib.sha256()
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
        return sha256.hexdigest()


def diff(f1, f2):
    """Returns boolean indicating whether or not the given files are different."""
    return bool(run("diff {} {}".format(shlex.quote(f1), shlex.quote(f2))).exit())


def exists(*paths):
    """Asserts that all given paths exist."""
    for path in paths:
        log(f"Checking that {path} exists...")
        if not os.path.exists(path):
            raise Failure(f"{path} not found")


def import_checks(path):
    """Retrieve a Python module/package from (relative) path"""
    dir = internal.check_dir / path
    name = dir.name

    file = internal.parse_config(dir)["checks"]
    mod = internal.import_file(name, (dir / file).resolve())
    sys.modules[name] = mod
    return mod



# TODO: Add docstrings to methods
class Process:
    """ Wrapper class for pexpect child process. """

    def __init__(self, proc):
        self.process = proc

    def stdin(self, line, prompt=True, timeout=3):
        """Send line to stdin
        If prompt is set to True (False by default) expect a prompt, any character in stdout
        waits until timeout for a prompt."""
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
