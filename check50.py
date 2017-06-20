#!/usr/bin/env python3

import argparse
import importlib
import inspect
import json
import os
import pexpect
import re
import shutil
import sys
import tempfile
import traceback
import unittest

from functools import wraps
from termcolor import cprint

import config

# TODO: pull checks directory from repo?
checks_dir = os.path.join(os.getcwd().split("check50")[0] + "check50", "checks")

def main():

    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier", nargs=1)
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-l", "--log", action="store_true")
    args = parser.parse_args()
    identifier = args.identifier[0]
    files = args.files

    # copy all files to temporary directory
    config.tempdir = tempfile.mkdtemp()
    src_dir = os.path.join(config.tempdir, "_")
    os.mkdir(src_dir)
    if len(files) == 0:
        files = os.listdir()
    for filename in files:
        if os.path.exists(filename):
            if os.path.isfile(filename):
                shutil.copy(filename, src_dir)
            else:
                shutil.copytree(filename, os.path.join(src_dir, filename))
        else:
            err("File {} not found.".format(filename))

    # import the checks and identify check class
    identifier = "checks.{}".format(identifier)
    try:
        checks = importlib.import_module(identifier)
    except ImportError:
        err("Invalid identifier.")
    classes = [m[1] for m in inspect.getmembers(checks, inspect.isclass)
            if m[1].__module__ == identifier] 

    # ensure test module has a class of test cases
    if len(classes) == 0:
        err("Invalid identifier.")
    test_class = classes[0]

    # create and run the test suite
    suite = unittest.TestSuite()
    for case in config.test_cases:
        suite.addTest(test_class(case))
    results = TestResult()
    suite.run(results)
    cleanup()

    # print the results
    if args.debug:
        print_json(results)
    else:
        print_results(results, log=args.log)

def print_results(results, log=False):
    for result in results.results:
        if result["status"] == TestCase.PASS:
            cprint(":) {}".format(result["description"]), "green")
        elif result["status"] == TestCase.FAIL:
            cprint(":( {}".format(result["description"]), "red")
            if result["rationale"] != None:
                cprint("    {}".format(result["rationale"]), "red")
            if result["helpers"] != None:
                cprint("    {}".format(result["helpers"]), "red")
        elif result["status"] == TestCase.SKIP:
            cprint(":| {}".format(result["description"]), "yellow")
            cprint("    test skipped", "yellow")

        if log:
            for line in result["test"].log:
                print("    {}".format(line))

def print_json(results):
    output = {}
    for result in results.results:
        output.update({result["test"]._testMethodName : result["status"]})
    print(json.dumps(output))

def err(err):
    cleanup()
    cprint(err, "red")
    sys.exit(1)

def cleanup():
    """Remove temporary files at end of test."""
    shutil.rmtree(config.tempdir)

class TestResult(unittest.TestResult):
    results = []
    
    def __init__(self):
        super().__init__(self)

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
        cprint("check50 ran into an error while running checks.", "red")
        cleanup()
        print(err[1])
        traceback.print_tb(err[2])
        sys.exit(1)

# decorator for checks
def check(dependency=None):
    def decorator(func):

        # add test to list of test, in order of declaration
        config.test_cases.append(func.__name__)
        @wraps(func)
        def wrapper(self):

            # check if dependency failed
            if dependency and config.test_results.get(dependency) != TestCase.PASS:
                self.result = config.test_results[func.__name__] = TestCase.SKIP
                return

            # move files into this check's directory 
            self.dir = dst_dir = os.path.join(config.tempdir, self._testMethodName)
            if dependency:
                src_dir = os.path.join(config.tempdir, dependency)
            else:
                src_dir = os.path.join(config.tempdir, "_") 
            shutil.copytree(src_dir, dst_dir)

            # run the test, catch failures
            try:
                func(self)
            except Error as e:
                self.rationale = e.rationale
                self.helpers = e.helpers
                return

            # if test didn't fail, then it passed
            if config.test_results.get(func.__name__) == None:
                self.result = config.test_results[func.__name__] = TestCase.PASS

        return wrapper 
    return decorator 

# generic class to represent a file
class File():
    def __init__(self, filename):
        self.filename = filename

# class to wrap errors
class Error(Exception):
    def __init__(self, rationale=None, helpers=None):
        def raw(s):
            if type(s) != str:
                return s
            s = repr(s)  # get raw representation of string
            s = s[1:len(s) - 1]  # strip away quotation marks
            if len(s) > 15:
                s = s[:15] + "..."  # truncate if too long
            return "\"{}\"".format(s)
        if type(rationale) == tuple:
            rationale = "Expected {}, not {}.".format(raw(rationale[1]), raw(rationale[0]))
        self.rationale = rationale 
        self.helpers = helpers

# wrapper class for pexpect child
class Child():
    def __init__(self, test, child):
        self.test = test
        self.child = child

    def stdin(self, line, prompt=True):
        if line != None:
            self.test.log.append("Sending input {}...".format(line))
        else:
            self.test.log.append("Sending Ctrl-D...")

        if prompt:
            self.child.expect(".+")

        if line != None:
            self.child.sendline(line)
        else:
            self.child.sendcontrol('d')
        return self

    def stdout(self, output=None, str_output=None):
        self.test.log.append("Checking for output {}...".format(str_output))
        result = self.child.read().replace("\r\n", "\n").lstrip("\n")
        if output == None:
            return result
        if type(output) == File:
            correct = open(os.path.join(checks_dir, output.filename), "r").read()
            if result != correct:
                raise Error((result, correct))
        else: # regex
            r = re.compile(output)
            if not r.match(result):
                raise Error((result, str_output))
        return self

    def reject(self):
        self.test.log.append("Checking that input was rejected...")
        try:
            self.child.expect(".+")
            self.child.sendline("")
        except OSError:
            self.test.fail()
        return self

    def exit(self, code=None):
        self.child.wait()
        self.exitstatus, self.output = self.child.exitstatus, self.child.read()
        self.child.close()
        if code != None:
            self.test.log.append("Checking that program exited with status {}...".format(code))
            if self.exitstatus != code:
                raise Error("Expected exit code {}, not {}".format(code, self.exitstatus))
        return self

    def kill(self):
        self.child.close(force=True)
        return self

class TestCase(unittest.TestCase):
    PASS = True
    FAIL = False 
    SKIP = None

    def __init__(self, method_name):
        super().__init__(method_name)
        self.result = self.FAIL
        self.rationale = None
        self.helpers = None
        self.log = []

    def checkfile(self, filename):
        """Gets the contents of a check file."""
        contents = open(os.path.join(checks_dir, filename)).read()
        return contents

    def exists(self, filename):
        """Asserts that filename exists."""
        self.log.append("Checking that {} exists...".format(filename))
        os.chdir(self.dir)
        if not os.path.isfile(filename):
            raise Error("File {} not found.".format(filename))

    def spawn(self, cmd, status=0, env=None):
        """Asserts that cmd returns with code status (0 by default)."""
        self.log.append("Running {}...".format(cmd))
        os.chdir(self.dir)
        if env == None:
            env = {}
        env = os.environ.update(env)
        child = pexpect.spawn(cmd, encoding="utf-8", echo=False, env=env)
        return Child(self, child)

    def include(self, path):
        """Copies a file to the temporary directory."""
        shutil.copy(os.path.join(checks_dir, path), self.dir)

    def append_code(self, filename, codefile):
        code = open(os.path.join(checks_dir, codefile.filename), "r")
        contents = code.read()
        code.close()
        f = open(os.path.join(self.dir, filename), "a")
        f.write(contents)
        f.close()

    def fail(self, rationale):
        self.result = self.FAIL
        self.rationale = rationale
        super().fail()

if __name__ == "__main__":
    main()
