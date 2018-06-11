from contextlib import contextmanager
from functools import wraps
import os
import re
import signal
import time

import shutil
from shlex import quote
import pexpect
from pexpect.exceptions import EOF, TIMEOUT

from . import internal


def run(command, env=None):
    """Runs a command with the specified environment."""
    log(f"running {command}...")

    if env is None:
        env = {}

    # Workaround for OSX pexpect bug http://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits
    # Workaround from https://github.com/pexpect/pexpect/issues/373
    command = "bash -c {}".format(quote(command))
    child = pexpect.spawnu(command, encoding="utf-8", echo=False, env=env)

    return Process(child)


_log = []
def log(line):
    """Add line to check log."""
    _log.append(line)


def include(*paths):
    """Copies a file from the check directory to the current directory."""
    cwd = os.getcwd()
    with cd(internal.check_dir):
        for path in paths:
            _copy(path, cwd)


def hash(self, file):
    """Hashes a file using SHA-256."""

    # Get filename
    try:
        file = file.name
    except AttributeError:
        pass

    exists(file)

    # https://stackoverflow.com/a/22058673
    with open(file, "rb"):
        sha256 = hashlib.sha256()
        for block in iter(lambda: f.read(65536), ""):
            sha256.update(data)
        return sha256.hexdigest()


def diff(self, f1, f2):
    """Returns boolean indicating whether or not the files are different"""
    try:
        f1 = f1.name
    except AttributeError:
        pass

    try:
        f2 = f2.name
    except AttributeError:
        pass

    return bool(run("diff {} {}".format(quote(f1), quote(f2))).exit())


def exists(*paths):
    """Asserts that all paths exist."""
    for path in paths:
        log(f"Checking that {path} exists...")
        if not os.path.exists(path):
            raise Failure(f"{path} not found")


class Process:
    """ Wrapper class for pexpect child process. """

    def __init__(self, proc):
        self.process = proc

    def stdin(self, line, prompt=True, timeout=3):
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

    def stdout(self, output=None, str_output=None, timeout=3):
        if output is None:
            return self._wait(timeout)._output

        # Files should be interpreted literally, anything else shouldn't be.
        try:
            output = output.read()
        except AttributeError:
            expect = self.process.expect
        else:
            expect = self.process.expect_exact

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
        log("checking that input was rejected...")
        try:
            self._wait(timeout)
        except Failure as e:
            if not isinstance(e.__context__, TIMEOUT):
                raise
        else:
            raise Failure("expected program to reject input, but it did not")
        return self

    def exit(self, code=None, timeout=5):
        self._wait(timeout)

        if code is None:
            return self.exitcode

        log(f"checking that program exited with status {code}...")
        if self.exitcode != code:
            raise Failure(f"expected exit code {code}, not {self.exitcode}")
        return self

    def kill(self):
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
            e = Failure("timed out while waiting for program to exit")
            e.__context__ = TIMEOUT(timeout)
            raise e

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
                    actual=self.actual
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
    """Copy src to dst, copying recursively if src is a directory"""
    try:
        shutil.copy(src, dst)
    except IsADirectoryError:
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.copytree(src, dst)
