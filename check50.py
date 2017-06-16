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
import unittest2

from functools import wraps
from termcolor import cprint

import config

# TODO: pull checks directory from repo?
checks_dir = os.path.join(os.getcwd(), "checks")

def main():

    # parse command line arguments
    parser = argparse.ArgumentParser(description="This is check50.")
    parser.add_argument("identifier", nargs=1)
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-l", "--log", action="store_true")
    args = parser.parse_args()
    identifier = args.identifier[0]
    files = args.files

    # move all files to temporary directory
    config.tempdir = tempfile.mkdtemp()
    src_dir = os.path.join(config.tempdir, "_")
    os.mkdir(src_dir)
    for filename in files:
        if os.path.isfile(filename):
            shutil.copy(filename, src_dir)
        else:
            error("File {} not found.".format(filename))

    # import the checks and identify check class
    identifier = "checks.{}".format(identifier)
    try:
        checks = importlib.import_module(identifier)
    except ImportError:
        error("Invalid identifier.")
    classes = [m[1] for m in inspect.getmembers(checks, inspect.isclass)
            if m[1].__module__ == identifier] 
    if len(classes) == 0:
        error("Invalid identifier.")
    test_class = classes[0]

    # create and run the test suite
    suite = unittest2.TestSuite()
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
        if result["status"] == Test.PASS:
            cprint(":) {}".format(result["description"]), "green")
        elif result["status"] == Test.FAIL:
            cprint(":( {}".format(result["description"]), "red")
            if result["rationale"] != None:
                cprint("    {}".format(result["rationale"]), "red")
            if result["helpers"] != None:
                cprint("    {}".format(result["helpers"]), "red")
        elif result["status"] == Test.SKIP:
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

def error(err):
    cleanup()
    cprint(err, "red")
    sys.exit(1)

def cleanup():
    """Remove temporary files at end of test."""
    shutil.rmtree(config.tempdir)

class TestResult(unittest2.TestResult):
    results = []
    
    def __init__(self):
        super().__init__(self)

    def addSuccess(self, test):
        """Handle completion of test, regardless of outcome."""
        self.results.append({
            "status": test.result,
            "test": test,
            "description": test.shortDescription(),
            "rationale": test.rationale,
            "helpers": test.helpers,
            "log": test.log
        })

    def addError(self, test, err):
        cprint("check50 ran into an error while running checks.", "red")
        print(err[1])
        traceback.print_tb(err[2])
        sys.exit(1)

# decorator for checks
def check(dependency=None):
    def decorator(func):
        config.test_cases.append(func.__name__)
        @wraps(func)
        def wrapper(self):

            # check  if dependency failed
            if dependency and config.test_results.get(dependency) != Test.PASS:
                self.result = config.test_results[func.__name__] = Test.SKIP
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
                self.result = config.test_results[func.__name__] = Test.PASS

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
            s = repr(s)  # get raw representation of string
            s = s[1:len(s) - 1]  # strip away quotation marks
            if len(s) > 15:
                s = s[:15] + "..."  # truncate if too long
            return s
        if type(rationale) == tuple:
            rationale = "Expected \"{}\", not \"{}\".".format(raw(rationale[1]), raw(rationale[0]))
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

class Test(unittest2.TestCase):
    PASS = 1
    FAIL = 0
    SKIP = -1

    def __init__(self, method_name):
        super().__init__(method_name)
        self.result = self.FAIL
        self.rationale = None
        self.helpers = None
        self.log = []

    def checkfile(self, filename):
        """gets contents of a check file"""
        contents = open(os.path.join(checks_dir, filename)).read()
        return contents

    def exists(self, filename):
        """asserts that filename exists"""
        self.log.append("Checking that {} exists...".format(filename))
        os.chdir(self.dir)
        if not os.path.isfile(filename):
            raise Error("File {} not found.".format(filename))

    def spawn(self, cmd, status=0):
        """asserts that cmd returns with code status (0 by default)"""
        self.log.append("Running {}...".format(cmd))
        os.chdir(self.dir)
        child = pexpect.spawn(cmd, encoding="utf-8", echo=False)
        return Child(self, child)

    def include(self, path):
        """copies a file to the temporary directory"""
        shutil.copy(os.path.join(checks_dir, path), self.dir)

    def fail(self, rationale):
        self.result = self.FAIL
        self.rationale = rationale
        super().fail()

if __name__ == "__main__":
    main()
