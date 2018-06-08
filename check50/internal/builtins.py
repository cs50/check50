from functools import wraps
import os
import re
import signal
import time

import shutil
from shlex import quote
import pexpect
from pexpect.exceptions import EOF, TIMEOUT

from . import globals
from . import register
from .errors import Error, InternalError, Mismatch
from .logger import log

def run(command, env=None):
    """ Runs a command. """
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


def include(*paths):
    """Copies a file to the temporary directory."""
    cwd = os.getcwd()
    with cd(globals.check_dir):
        for path in paths:
            copy(path, cwd)


def match(actual, expected, str_output = ""):
    if not str_output:
        str_output = expected

    # Files should be interpreted literally, anything else shouldn't be.
    try:
        expected = expected.read()
    except AttributeError:
        is_match = re.match(expected, actual)
    else:
        is_match = expected == actual

    if not is_match:
        return False

    # If we expected EOF and we still got output, report an error.
    if output == EOF and re.match(re.compile(".+" + EOF, re.DOTALL), actual):
        return False

    return True

def exists(*paths):
    """Asserts that all paths exist."""
    for path in paths:
        log(f"Checking that {path} exists...")
        if not os.path.exists(path):
            raise Error(f"{path} not found")


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
                self.process.expect(".+", timeout=timeout)
            except (TIMEOUT, EOF):
                raise Error("expected prompt for input, found none")
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
            raise Error(Mismatch(str_output, result.replace("\r\n", "\n")))
        except TIMEOUT:
            raise Error(f"did not find {Mismatch.raw(str_output)}")
        except UnicodeDecodeError:
            raise Error("output not valid ASCII text")
        except Exception:
            raise Error("check50 could not verify output")

        # If we expected EOF and we still got output, report an error.
        if output == EOF and self.process.before:
            raise Error(Mismatch(EOF, self.process.before.replace("\r\n", "\n")))

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
    global _processes
    for p in _processes:
        p.kill()
    _processes = []
register.register_after(_stop_all)
