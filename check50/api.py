from functools import wraps
import os
import re
import signal
import time

import shutil
from shlex import quote
import pexpect
from pexpect.exceptions import EOF, TIMEOUT

from . import config
from . import internal
from .internal import log
from .errors import Error, InternalError, Mismatch

__all__ = ["run", "require", "log", "check", "Error", "Mismatch"]


def run(command, env=None):
    log(f"running {command}...")

    if env is None:
        env = {}

    env = os.environ.update(env)

    # Workaround for OSX pexpect bug http://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits
    # Workaround from https://github.com/pexpect/pexpect/issues/373
    command = "bash -c {}".format(quote(command))
    child = pexpect.spawnu(command, encoding="utf-8", echo=False, env=env)

    _processes.append(Process(child))
    return _processes[-1]

# should we take an (optional) str_output here? Don't want to log a regex necessarily
# TODO: rewrite
def match(actual, expected):

    # log("checking that  output \"{}\"...".format(expected))

    # Files should be interpreted literally, anything else shouldn't be.
    try:
        expected = expected.read()
    except AttributeError:
        expect = re.match(expected, actual)
    else:
        expect = expected == actual

    if not expect:
        raise Error(Mismatch(expected, actual.replace("\r\n", "\n")))

    # If we expected EOF and we still got output, report an error.
    if output == EOF and re.match(re.compile(".+" + EOF, re.DOTALL), actual):
        raise Error(Mismatch(EOF, actual))

def require(*paths):
    """Asserts that all paths exist."""
    for path in paths:
        log(f"Checking that {path} exists...")
        if not os.path.exists(path):
            raise Error(f"{path} not found")


# NOTE: this is here temporarily. Will get moved to runner.py
import enum
class Result(enum.Enum):
    Pass = True
    Fail = False
    Skip = None
    Error = None

# This is going to change quite a lot
# Decorator for checks
def check(dependency=None):
    def decorator(func):

        # add test to list of test, in order of declaration
        config.test_cases.append(func.__name__)

        @wraps(func)
        def wrapper():

            # Check if dependency failed.
            if dependency and config.test_results.get(dependency) is not Result.Pass:
                wrapper.result = config.test_results[func.__name__] = Result.Skip
                return

            # Move files into this check's directory.
            dst_dir = os.path.join(config.tempdir, func.__name__)
            src_dir = os.path.join(config.tempdir, dependency or "_")
            shutil.copytree(src_dir, dst_dir)

            os.chdir(dst_dir)
            # Run the test, catch failures.
            try:
                func()
            except Error as e:
                result = e.result
            else:
                result = Result.Pass

            config.test_results[func.__name__] = result

        wrapper._checks_sentinel = True
        return wrapper

    return decorator

class Process:
    """ Wrapper class for pexpect child process. """

    def __init__(self, process_reference):
        _processes.append(self)
        self.process = process_reference

    def stdin(self, line, prompt=True, timeout=3):
        if line == EOF:
            log("sending EOF...")
        else:
            log(f"sending input {line}...")

        if prompt:
            try:
                self.child.expect(".+", timeout=timeout)
            except (TIMEOUT, EOF):
                raise Error("expected prompt for input, found none")

        if line == EOF:
            self.child.sendeof()
        else:
            self.child.sendline(line)

        return self

    def stdout(self, output=None, str_output=None, timeout=3):
        if output is None:
            return self._wait(timeout)._output

        # Files should be interpreted literally, anything else shouldn't be.
        try:
            output = output.read()
        except AttributeError:
            expect = self.child.expect
        else:
            expect = self.child.expect_exact

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
            result = self.child.before + self.child.buffer
            if self.child.after != EOF:
                result += self.child.after
            raise Error(Mismatch(str_output, result.replace("\r\n", "\n")))
        except TIMEOUT:
            raise Error(f"did not find {Mismatch.raw(str_output)}")
        except UnicodeDecodeError:
            raise Error("output not valid ASCII text")
        except Exception:
            raise Error("check50 could not verify output")

        # If we expected EOF and we still got output, report an error.
        if output == EOF and self.child.before:
            raise Error(Mismatch(EOF, self.child.before.replace("\r\n", "\n")))

        return self

    def reject(self, timeout=1):
        log("checking that input was rejected...")
        try:
            self._wait(timeout)
        except Error as e:
            if not isinstance(e.__context__, TIMEOUT):
                raise
        else:
            raise Error("expected program to reject input, but it did not")
        return self

    def exit(self, code=None, timeout=5):
        self._wait(timeout)

        if code is None:
            return self.exitcode

        log(f"checking that program exited with status {code}...")
        if self.exitcode != code:
            raise Error(f"expected exit code {code}, not {self.exitcode}")
        return self

    def kill(self):
        self.process.close(force=True)
        return self

    def _wait(self, timeout=5):
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
                raise Error("output not valid ASCII text")
            else:
                out.append(bytes)
        else:
            e = Error("timed out while waiting for program to exit")
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
            raise Error("failed to execute program due to segmentation fault")

        self.exitcode = self.process.exitstatus
        return self

_processes = []
def _stop_all():
    for p in _processes:
        p.kill()
    _processes = []
internal.register_after(_stop_all)
