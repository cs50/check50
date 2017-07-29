#!/usr/bin/env python3

from __future__ import print_function

import argparse
import errno
import hashlib
import importlib
import inspect
import json
import os
import pexpect
import re
import requests
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import unittest
import xml.etree.cElementTree as ET

from backports.shutil_which import which
from distutils.version import StrictVersion
from functools import wraps
from pexpect.exceptions import EOF, TIMEOUT
from pkg_resources import DistributionNotFound, get_distribution, parse_version
from termcolor import cprint

import config


# Exports
__all__ = ["check", "Checks", "Child", "EOF", "Error", "File", "valgrind"]


def copy(src, dst):
    """Copy src to dst regardless, copying recursively if src is a directory"""
    try:
        shutil.copytree(src, os.path.join(dst, os.path.basename(src)))
    except IOError as e:
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            raise


# Internationalization
gettext.bindtextdomain("messages", os.path.join(sys.path[0], "locale"))
gettext.textdomain("messages")
_ = gettext.gettext


def main():

    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier", nargs=1)
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("-l", "--local", action="store_true")
    parser.add_argument("--log", action="store_true")
    parser.add_argument("--no-upgrade", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")

    main.args = parser.parse_args()
    identifier = main.args.identifier[0]
    files = main.args.files

    # check if installed as package
    try:
        distribution = get_distribution("check50")
    except DistributionNotFound:
        distribution = None

    # check for newer version on PyPi
    if distribution:
        res = requests.get("https://pypi.python.org/pypi/check50/json")
        pypi = res.json() if res.status_code == 200 else None
        version = StrictVersion(distribution.version)
        if pypi and not main.args.no_upgrade and StrictVersion(pypi["info"]["version"]) > version:

            # updade check50
            pip = "pip3" if sys.version_info >= (3, 0) else "pip"
            status = subprocess.call([pip, "install", "--upgrade", "check50"])

            # if update succeeded, re-run check50
            if status == 0:
                check50 = os.path.realpath(__file__)
                os.execv(check50, sys.argv + ["--no-update"])
            else:
                print(_("Could not update check50."), file=sys.stderr)

    if not main.args.local:
        try:

            # Submit to check50 repo.
            import submit50
        except ImportError:
            raise InternalError(_("submit50 is not installed. Install submit50 and run check50 again."))
        else:
            submit50.run.verbose = main.args.verbose
            prompts = {
                "confirmation": _("Are you sure you want to check these files?"),
                "submitting": _("Uploading"),
                "files_submit": _("Files that will be checked:"),
                "files_no_submit": _("Files that won't be checked:"),
                "print_success": False
            }
            username, commit_hash = submit50.submit("check50", identifier, prompts=prompts)

            # Wait until payload comes back with check data.
            print("Running checks...", end="")
            sys.stdout.flush()
            while True:
                res = requests.post("https://cs50.me/check50/status/{}/{}".format(username, commit_hash))
                if res.status_code != 200:
                    continue
                payload = res.json()
                if payload["complete"] and payload["checks"] != []:
                    break
                print(".", end="")
                sys.stdout.flush()
                time.sleep(2)
            print()

            # Print results from payload
            print_results(payload["checks"], main.args.log)
            print(_("Detailed Results:"), "https://cs50.me/check50/results/{}/{}".format(username, commit_hash))
            sys.exit(0)

    # copy all files to temporary directory
    config.tempdir = tempfile.mkdtemp()
    src_dir = os.path.join(config.tempdir, "_")
    os.mkdir(src_dir)
    if len(files) == 0:
        files = os.listdir()
    for filename in files:
        copy(filename, src_dir)

    # prepend cs50/ directory by default
    if identifier.split("/")[0].isdigit():
        identifier = os.path.join("cs50", identifier)

    # get checks directory
    config.check_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "checks", identifier)

    # import the checks and identify check class
    identifier = "checks.{}.checks".format(identifier.replace("/", "."))
    try:
        checks = importlib.import_module(identifier)
        test_class = next(m[1] for m in inspect.getmembers(checks, inspect.isclass)
                               if m[1].__module__ == identifier)
    except (ImportError, StopIteration):
        raise InternalError(_("Invalid identifier."))

    # create and run the test suite
    suite = unittest.TestSuite()
    for case in config.test_cases:
        suite.addTest(test_class(case))
    result = TestResult()
    suite.run(result)
    cleanup()

    # Get list of results from TestResult class
    results = result.results

    # print the results
    if main.args.full:  # both JSON and results
        sentinel = "\x1c" * 10
        print(sentinel)
        print_json(results)
        print(sentinel)
        print_results(results, log=main.args.log)
    elif main.args.debug:
        print_json(results)
    else:
        print_results(results, log=main.args.log)


def print_results(results, log=False):
    for result in results:
        if result["status"] == Checks.PASS:
            cprint(":) {}".format(result["description"]), "green")
        elif result["status"] == Checks.FAIL:
            cprint(":( {}".format(result["description"]), "red")
            if result["rationale"] is not None:
                cprint("    {}".format(result["rationale"]), "red")
        elif result["status"] == Checks.SKIP:
            cprint(":| {}".format(result["description"]), "yellow")
            cprint("    {}".format(result.get("rationale") or "check skipped"), "yellow")

        if log:
            for line in result["test"].log:
                print("    {}".format(line))



def print_json(results):
    output = []
    for result in results:
        output.append({
            "name": result["test"]._testMethodName,
            "status": result["status"],
            "rationale": result["rationale"],
            "description": result["description"],
            "helpers": result["helpers"],
            "log": result["test"].log
        })
    print(json.dumps(output))



def cleanup():
    """Remove temporary files at end of test."""
    if config.tempdir:
        shutil.rmtree(config.tempdir)



def excepthook(cls, exc, tb):
    cleanup()
    if cls is InternalError:
        cprint(exc.msg, "red")
    elif any(issubclass(cls, err) for err in [IOError, OSError]) and exc.errno == errno.ENOENT:
        cprint(_("File {} not found".format(exc.filename)), "red")
    else:
        cprint("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!", "red")

    if main.args.verbose:
        traceback.print_exception(cls, exc, tb)

sys.excepthook = excepthook


class TestResult(unittest.TestResult):
    results = []

    def __init__(self):
        super(TestResult, self).__init__(self)

    def addSuccess(self, test):
        """Handle completion of test, regardless of outcome."""
        self.results.append({
            "description": test.shortDescription(),
            "helpers": test.helpers,
            "log": test.log,
            "rationale": test.rationale,
            "status": test.result,
            "test": test
        })

    def addError(self, test, err):
        self.results.append({
            "description": test.shortDescription(),
            "helpers": test.helpers,
            "log": test.log,
            "rationale": err[1],
            "status": Checks.FAIL,
            "test": test
        })
        cprint(_("check50 ran into an error while running checks."), "red")
        print(err[1])
        traceback.print_tb(err[2])

def valgrind(func):
    if config.test_cases[-1] == func.__name__:
        frame = traceback.extract_stack(limit=2)[0]
        raise InternalError(_("Invalid check in {} on line {} of {}:\n"
                           "@valgrind must be placed below @check"\
                            .format(frame.name, frame.lineno, frame.filename)))
    @wraps(func)
    def wrapper(self):
        if not which("valgrind"):
            raise Error("valgrind not installed", result=Checks.SKIP)

        self._valgrind = True
        try:
            func(self)
            self._check_valgrind()
        finally:
            self._valgrind = False
    return wrapper


# decorator for checks
def check(dependency=None):
    def decorator(func):

        # add test to list of test, in order of declaration
        config.test_cases.append(func.__name__)
        @wraps(func)
        def wrapper(self):

            # check if dependency failed
            if dependency and config.test_results.get(dependency) != Checks.PASS:
                self.result = config.test_results[func.__name__] = Checks.SKIP
                self.rationale = "can't check until a frown turns upside down"
                return

            # move files into this check's directory
            self.dir = dst_dir = os.path.join(config.tempdir, self._testMethodName)
            src_dir = os.path.join(config.tempdir, dependency or "_")
            shutil.copytree(src_dir, dst_dir)

            os.chdir(self.dir)
            # run the test, catch failures
            try:
                func(self)
            except Error as e:
                self.rationale = e.rationale
                self.helpers = e.helpers
                result = e.result
            else:
                result = Checks.PASS

            self.result = config.test_results[func.__name__] = result

        return wrapper
    return decorator

class File():
    """Generic class to represent file in check directory."""
    def __init__(self, filename):
        self.filename = filename

    def read(self):
        with File._open(self.filename) as f:
            return f.read()

    @staticmethod
    def _open(file, mode="r"):
        if sys.version_info < (3, 0):
            return open(file, mode + "U")
        else:
            return open(file, mode, newline="\n")


class InternalError(Exception):
    """Error during execution of check50."""
    def __init__(self, msg):
        self.msg = msg


# wrapper class for pexpect child
class Child():
    def __init__(self, test, child):
        self.test = test
        self.child = child
        self.output = []
        self.exitstatus = None

    def stdin(self, line, prompt=True):
        if line == EOF:
            self.test.log.append(_("Sending EOF..."))
        else:
            self.test.log.append(_("Sending input {}...".format(line)))

        if prompt:
            self.child.expect(".+")

        if line == EOF:
            self.child.sendeof()
        else:
            self.child.sendline(line)
        return self

    def stdout(self, output=None, str_output=None, timeout=2):
        if output is None:
            return self.wait(timeout).output

        # Files should be interpreted literally, anything else shouldn't be
        try:
            output = output.read()
        except AttributeError:
            expect = self.child.expect
        else:
            expect = self.child.expect_exact

        if output == EOF:
            str_output = "EOF"
        else:
            if str_output is None:
                str_output = output
            output = output.replace("\n", "\r\n")


        self.test.log.append(_("Checking for output \"{}\"...".format(str_output)))

        try:
            expect(output, timeout=timeout)
        except EOF:
            result = self.child.before + self.child.buffer
            if self.child.after != EOF:
                result += self.child.after
            raise Error((result.replace("\r\n", "\n"), str_output))
        except TIMEOUT:
            raise Error(_("Check timed out while waiting for {}").format(str_output))

        # If we expected EOF and we still got output, report an error
        if output == EOF and self.child.before:
            raise Error((self.child.before.replace("\r\n", "\n"), EOF))

        return self

    def reject(self):
        self.test.log.append(_("Checking that input was rejected..."))
        try:
            self.child.expect(".+")
            self.child.sendline("")
        except OSError:
            self.test.fail()
        return self

    def exit(self, code=None, timeout=2):
        self.wait(timeout)

        if code is None:
            return self.exitstatus

        self.test.log.append(_("Checking that program exited with status {}...".format(code)))
        if self.exitstatus != code:
            raise Error(_("Expected exit code {}, not {}".format(code, self.exitstatus)))
        return self

    def wait(self, timeout=2):
        if timeout is None:
            timeout = float("inf")

        end = time.time() + timeout
        while time.time() <= end:
            if not self.child.isalive():
                break
            try:
                bytes = self.child.read_nonblocking(size=1024, timeout=0)
            except TIMEOUT:
                pass
            except EOF:
                break
            else:
                self.output.append(bytes)
        else:
            raise Error("Timed out while waiting for program to exit")

        # Read any remaining data in pipe
        while True:
            try:
                bytes = self.child.read_nonblocking(size=1024, timeout=0)
            except (TIMEOUT, EOF):
                break
            else:
                self.output.append(bytes)

        self.output = "".join(self.output).replace("\r\n", "\n").lstrip("\n")
        self.kill()
        self.exitstatus = self.child.exitstatus
        return self

    def kill(self):
        self.child.close(force=True)
        return self

class Checks(unittest.TestCase):
    PASS = True
    FAIL = False
    SKIP = None

    _valgrind_log = "valgrind.xml"
    _valgrind = False

    def tearDown(self):
        while self.children:
            self.children.pop().kill()

    def __init__(self, method_name):
        super(Checks, self).__init__(method_name)
        self.result = self.FAIL
        self.rationale = None
        self.helpers = None
        self.log = []
        self.children = []

    def diff(self, f1, f2):
        """Returns boolean indicating whether or not the files are different"""
        if type(f1) == File:
            f1 = f1.filename
        if type(f2) == File:
            f2 = f2.filename
        return bool(self.spawn("diff {} {}".format(shlex.quote(f1), shlex.quote(f2)))
                        .wait(timeout=None)
                        .exitstatus)

    def exists(self, *filenames):
        """Asserts that filename (or all filenames) exists."""
        for filename in filenames:
            self.log.append(_("Checking that {} exists...".format(filename)))
            if not os.path.exists(filename):
                raise Error(_("File {} not found.".format(filename))

    def hash(self, filename):
        """Hashes a file using SHA-256."""

        # Assert that file exists.
        if type(filename) == File:
            filename = filename.filename
        Checks.exists(self, filename)

        # https://stackoverflow.com/a/22058673
        sha256 = hashlib.sha256()
        with open(filename, "rb") as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()

    def spawn(self, cmd, env=None):
        """Spawns a new child process."""
        if self._valgrind:
            self.log.append(_("Running valgrind {}...".format(cmd)))
            cmd = "valgrind --show-leak-kinds=all --xml=yes --xml-file={} -- {}" \
                        .format(os.path.join(self.dir, self._valgrind_log), cmd)
        else:
            self.log.append(_("Running {}...").format(cmd))

        if env is None:
            env = {}
        env = os.environ.update(env)

        # Workaround for OSX pexpect bug http://pexpect.readthedocs.io/en/stable/commonissues.html#truncated-output-just-before-child-exits
        # Workaround from https://github.com/pexpect/pexpect/issues/373
        cmd = "bash -c {}".format(shlex.quote(cmd))
        if sys.version_info < (3, 0):
            child = pexpect.spawn(cmd, echo=False, env=env)
        else:
            child = pexpect.spawnu(cmd, encoding="utf-8", echo=False, env=env)

        self.children.append(Child(self, child))
        return self.children[-1]

    def include(self, *paths):
        """Copies a file to the temporary directory."""
        cwd = os.getcwd()
        try:
            os.chdir(config.check_dir)
            for path in paths:
                copy(path, cwd)
        finally:
            os.chdir(cwd)

    def append_code(self, filename, codefile):
        with open(codefile.filename, "r") as code, \
                open(os.path.join(self.dir, filename), "a") as f:
            f.write("\n")
            f.write(code.read())

    def replace_fn(self, old_fn, new_fn, file):
        self.spawn("sed -i='' -e 's/callq\t_{}/callq\t_{}/g' {}".format(old_fn, new_fn, file))
        self.spawn("sed -i='' -e 's/callq\t{}/callq\t{}/g' {}".format(old_fn, new_fn, file))

    def _check_valgrind(self):
        """Log and report any errors encountered by valgrind"""
        # Load XML file created by valgrind
        xml = ET.ElementTree(file=os.path.join(self.dir, self._valgrind_log))

        self.log.append(_("Checking for valgrind errors... "))

        # Ensure that we don't get duplicate error messages
        reported = set()
        for error in xml.iterfind("error"):
            # Type of error valgrind encountered
            kind = error.find("kind").text

            # Valgrind's error message
            what = error.find("xwhat/text" if kind.startswith("Leak_") else "what").text

            # Error message that we will report
            msg = ["\t", what]

            # Find first stack frame within student's code
            for frame in error.iterfind("stack/frame"):
                obj = frame.find("obj")
                if obj is not None and os.path.dirname(obj.text) == self.dir:
                    location = frame.find("file"), frame.find("line")
                    if None not in location:
                        msg.append(": (file: {}, line: {})".format(location[0].text, location[1].text))
                    break

            msg = "".join(msg)
            if msg not in reported:
                self.log.append(msg)
                reported.add(msg)

        # Only raise exception if we encountered errors
        if reported:
            raise Error(_("Valgrind check failed. "
                          "Rerun with --log for more information."))


class Error(Exception):
    """Class to wrap errors in students' checks."""
    def __init__(self, rationale=None, helpers=None, result=Checks.FAIL):
        def raw(s):

            if type(s) == list:
                s = "\n".join(s)

            if s == EOF:
                return "EOF"

            s = repr(s)  # get raw representation of string
            s = s[1:-1]  # strip away quotation marks
            if len(s) > 15:
                s = s[:15] + "..."  # truncate if too long
            return "\"{}\"".format(s)
        if type(rationale) == tuple:
            rationale = _("Expected {}, not {}.".format(raw(rationale[1]), raw(rationale[0])))
        self.rationale = rationale
        self.helpers = helpers
        self.result = result

if __name__ == "__main__":
    main()
