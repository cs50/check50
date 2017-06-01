#!/usr/bin/env python3

import argparse
import importlib
import inspect
import os
import pexpect
import re
import sys
import traceback
import unittest2

from functools import wraps
from termcolor import cprint

def main():

    # parse command line arguments
    parser = argparse.ArgumentParser(description="This is check50.")
    parser.add_argument("identifier", nargs=1)
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    identifier = args.identifier[0]
    files = args.files

    # import the checks and identify check class
    identifier = "checks.{}".format(identifier)
    try:
        checks = importlib.import_module(identifier)
    except ImportError:
        print("Invalid identifier.")
        sys.exit(1)
    classes = [m[1] for m in inspect.getmembers(checks, inspect.isclass)
            if m[1].__module__ == identifier] 
    if len(classes) == 0:
        print("There are currently no checks for this problem.")
        sys.exit(2)
    test_class = classes[0]

    # create and run the test suite
    suite = unittest2.TestSuite()
    test_cases = getattr(checks, "test_cases")
    for case in test_cases:
        suite.addTest(test_class(case))
    results = TestResult()
    suite.run(results)

    # remove generated files at end of test
    if hasattr(checks, "remove"):
        for filename in getattr(checks, "remove"):
            if os.path.isfile(filename):
                os.remove(filename)

    # print the results
    print_results(results)

def print_results(results):
    for result in results.results:
        if result["status"] == Test.PASS:
            cprint(":) {}".format(result["description"]), "green")
        elif result["status"] == Test.FAIL:
            cprint(":( {}".format(result["description"]), "red")
            if result["error"] != None:
                cprint("    {}".format(result["error"]), "red")
        elif result["status"] == Test.SKIP:
            cprint(":| {}".format(result["description"]), "yellow")
            cprint("    test skipped", "yellow")

class TestResult(unittest2.TestResult):
    results = []
    
    def __init__(self):
        super().__init__(self)

    def addSuccess(self, test):
        self.results.append({
            "status": test.result,
            "description": test.shortDescription()
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results.append({
            "status": test.result, 
            "description": test.shortDescription(),
            "error": test.rationale
        })

    def addError(self, test, err):
        super().addFailure(test, err)
        self.results.append({
            "status": test.result,
            "description": test.shortDescription(),
            "error": test.rationale
        })

# decorator for checks
def check(*args):
    def decorator(func):
        Test.test_cases.append(func.__name__)
        @wraps(func)
        def wrapper(self):

            # check over all dependencies
            for dependency in args:
                if Test.test_results.get(dependency) != Test.PASS:
                    self.result = Test.test_results[func.__name__] = Test.SKIP
                    return
            
            # override assert method
            unittest_assert = self.assertTrue
            def assertTrue(expr):
                if expr == False:
                    self.result = Test.test_results[func.__name__] = Test.FAIL
                unittest_assert(expr)
            self.assertTrue = assertTrue

            # run the test
            func(self)

            # if test didn't fail, then it passed
            if Test.test_results.get(func.__name__) == None:
                self.result = Test.test_results[func.__name__] = Test.PASS

        return wrapper 
    return decorator 

# generic class to represent a file
class File():
    def __init__(self, filename):
        self.filename = filename

class Test(unittest2.TestCase):
    PASS = 1
    FAIL = 0
    SKIP = -1
    test_cases = []
    test_results = {}

    def __init__(self, method_name):
        super().__init__(method_name)
        self.result = self.FAIL
        self.rationale = None

    def check_exists(self, filename):
        """asserts that filename exists"""
        self.assertTrue(os.path.isfile(filename))

    def check_exitstatus(self, cmd, status):
        """asserts that cmd returns with code status"""
        result, _ = self.execute(cmd)
        self.assertTrue(result == status)
    
    def check_compiles(self, cmd):
        """asserts that cmd returns status 0"""
        self.check_exitstatus(cmd, 0)

    def check_output(self, cmd, text, output):
        """
        asserts that cmd, when passed text as input, produces output

        Parameters:
            text - string input or list of string inputs
            output - string, regex, or File indicating desired output
        """
        child = self.spawn(cmd)

        # if there's input, provide it
        if text != None:
            if type(text) != list:
                text = [text]
            # if multiple inputs, ensure prompts for all 
            for item in text:
                child.expect(".+")
                child.sendline(item)
        result = self.output(child)

        # check output depending on if regex, file, or string
        if type(output) == re._pattern_type:
            self.assertTrue(output.match(result) != None)
        elif type(output) == File:
            correct = open(output.filename, "r").read()
            self.assertTrue(result == correct)
        else:
            self.assertTrue(result == output)
    
    # TODO: figure out how to reject on waiting for stdin
    def check_reject(self, cmd, text):
        """asserts that cmd rejects input text"""
        child = self.spawn(cmd)
        child.expect(".+")
        child.sendline(text)
        child.expect(".+")
        try:
            child.sendline("")
        except OSError:
            self.fail()
    
    # TODO: handle timeouts
    def execute(self, cmd):
        """runs cmd and returns a tuple of (exit status, output)"""
        child = pexpect.spawn(cmd, encoding="utf-8", echo=False)
        child.wait()
        return child.exitstatus, child.read()

    def output(self, child):
        """reads output from a spawned pexpect, stripping starting newlines"""
        return child.read().lstrip("\n").replace("\r\n", "\n")

    def spawn(self, cmd):
        """spawns a child application"""
        child = pexpect.spawn(cmd, encoding="utf-8", echo=False)
        return child

if __name__ == "__main__":
    main()
