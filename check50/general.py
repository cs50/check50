import internal_api
import config
import os
import shutil
import time
import re
import signal
from errors import Error, InternalError, Mismatch
from functools import wraps
import pexpect
from pexpect.exceptions import EOF, TIMEOUT
try:
    from shlex import quote
except ImportError:
    from pipes import quote

__all__ = ["run", "match", "require", "log", "help", "fail", "check"]

_SKIP = "SKIP"
_PASS = "PASS"

def run(command):
    log(f"running {command}")

    env = os.environ.update({})

    # Workaround for OSX pexpect bug http://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits
    # Workaround from https://github.com/pexpect/pexpect/issues/373
    command = "bash -c {}".format(quote(command))
    child = pexpect.spawnu(command, encoding="utf-8", echo=False, env=env)

    return Process(child)

def match(actual, expected):
    if expected == EOF:
        log("checking for EOF...")
    else:
        log("checking for output \"{}\"...".format(expected))

    # Files should be interpreted literally, anything else shouldn't be.
    try:
        expected = expected.read()
    except AttributeError:
        expect = lambda : bool(re.match(expected, actual))
    else:
        expect = lambda : expected == actual

    if not expect():
        return fail(Mismatch(expected, actual.replace("\r\n", "\n")))

    # If we expected EOF and we still got output, report an error.
    if output == EOF and re.match(re.compile(".+" + EOF, re.DOTALL), actual):
        return fail(Mismatch(EOF, actual))

    return self

def require(*paths):
    """Asserts that all paths exist."""
    for path in paths:
        log("Checking that {} exists...".format(path))
        if not os.path.exists(path):
            raise Error("{} not found".format(path))

def log(line):
    internal_api.log(line)

def help(self, message):
    internal_api.set_help(message)

def fail(msg):
    raise Error(f"failed: {msg}")

# Decorator for checks
def check(dependency=None):
    def decorator(func):

        # add test to list of test, in order of declaration
        config.test_cases.append(func.__name__)

        @wraps(func)
        def wrapper():

            # Check if dependency failed.
            if dependency and config.test_results.get(dependency) != _PASS:
                wrapper.result = config.test_results[func.__name__] = _SKIP
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
                result = _PASS

            config.test_results[func.__name__] = result

        wrapper._checks_sentinel = True
        return wrapper

    return decorator

# Wrapper class for pexpect child
class Process:
    def __init__(self, process_reference):
        _processes.append(self)
        self.process = process_reference

    def stdin(self, line, timeout=3):
        log("sending input {}...".format(line))
        self.process.sendline(line)
        return self

    def stdout(self, expected=None, timeout=3):
        self._get(timeout)
        if self._output:
            match(self._output, expected)
        return self

    def reject(self, timeout=1):
        log("checking that input was rejected...")
        try:
            self._get(timeout)
        except Error as e:
            if not isinstance(e.__context__, TIMEOUT):
                raise
        else:
            fail("expected program to reject input, but it did not")
        return self

    def exit(self, code=None, timeout=5):
        self._get(timeout)

        if code is None:
            return self._exitcode

        log("checking that program exited with status {}...".format(code))
        if self._exitcode != code:
            fail("expected exit code {}, not {}".format(code, self.status.exit))
        return self

    def _get(self, timeout=5):
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
                return fail("output not valid ASCII text")
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
        self._stop()

        if self.process.signalstatus == signal.SIGSEGV:
            return fail("failed to execute program due to segmentation fault")

        self._exitcode = self.process.exitstatus
        return self

    def _stop(self):
        self.process.close(force=True)
        return self

_processes = []
def _stop_all():
    for p in _processes:
        p._stop()
    _processes = []
