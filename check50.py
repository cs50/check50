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

def main():

    # parse command line arguments
    parser = argparse.ArgumentParser(description="This is check50.")
    parser.add_argument("identifier", nargs=1)
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()
    identifier = args.identifier[0]
    files = args.files

    # move all files to temporary directory
    for filename in files:
        if os.path.isfile(filename):
            shutil.copy(filename, config.tempdir)
        else:
            error("File {} not found.".format(filename))
            sys.exit(1)

    # import the checks and identify check class
    identifier = "checks.{}".format(identifier)
    try:
        checks = importlib.import_module(identifier)
    except ImportError:
        error("Invalid identifier.")
    classes = [m[1] for m in inspect.getmembers(checks, inspect.isclass)
            if m[1].__module__ == identifier] 
    if len(classes) == 0:
        error("There are currently no checks for this problem.")
    test_class = classes[0]

    # create and run the test suite
    suite = unittest2.TestSuite()
    for case in config.test_cases:
        suite.addTest(test_class(case))
    results = TestResult()
    suite.run(results)

    # remove temporary files at end of test
    shutil.rmtree(config.tempdir)

    # print the results
    if args.debug:
        print_json(results)
    else:
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

def print_json(results):
    output = {}
    for result in results.results:
        output.update({result["test"]._testMethodName : result["status"]})
    print(json.dumps(output))

def error(err):
    cprint(err, "red")
    sys.exit(1)

class TestResult(unittest2.TestResult):
    results = []
    
    def __init__(self):
        super().__init__(self)

    def addSuccess(self, test):
        self.results.append({
            "status": test.result,
            "test": test,
            "description": test.shortDescription()
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results.append({
            "status": test.result, 
            "test": test,
            "description": test.shortDescription(),
            "error": test.rationale
        })

    def addError(self, test, err):
        print("Error {}".format(err))
        print("{}".format(traceback.print_tb(err[2])))
        super().addFailure(test, err)
        self.results.append({
            "status": test.result,
            "test": test,
            "description": test.shortDescription(),
            "error": test.rationale
        })

# decorator for checks
def check(*args):
    def decorator(func):
        config.test_cases.append(func.__name__)
        @wraps(func)
        def wrapper(self):

            # check over all dependencies
            for dependency in args:
                if config.test_results.get(dependency) != Test.PASS:
                    self.result = config.test_results[func.__name__] = Test.SKIP
                    return
            
            # override assert method
            unittest_assert = self.assertTrue
            def assertTrue(expr):
                if expr == False:
                    self.result = config.test_results[func.__name__] = Test.FAIL
                unittest_assert(expr)
            self.assertTrue = assertTrue

            # run the test
            func(self)

            # if test didn't fail, then it passed
            if config.test_results.get(func.__name__) == None:
                self.result = config.test_results[func.__name__] = Test.PASS

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

    def __init__(self, method_name):
        super().__init__(method_name)
        self.result = self.FAIL
        self.rationale = None

    def exists(self, filename):
        """asserts that filename exists"""
        os.chdir(config.tempdir)
        self.assertTrue(os.path.isfile(filename))

    def spawn(self, cmd, status=0):
        """asserts that cmd returns with code status (0 by default)"""
        result, _ = self.execute(cmd)
        self.assertTrue(result == status)

    def check_output(self, cmd, text, output):
        """
        asserts that cmd, when passed text as input, produces output

        Parameters:
            text - string input or list of string inputs
            output - string, regex, or File indicating desired output
        """
        child = self.spawnProcess(cmd)

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
        child = self.spawnProcess(cmd)
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
        os.chdir(config.tempdir)
        child = pexpect.spawn(cmd, encoding="utf-8", echo=False)
        child.wait()
        return child.exitstatus, child.read()

    def output(self, child):
        """reads output from a spawned pexpect, stripping starting newlines"""
        return child.read().lstrip("\n").replace("\r\n", "\n")

    def spawnProcess(self, cmd):
        """spawns a child application"""
        os.chdir(config.tempdir)
        child = pexpect.spawn(cmd, encoding="utf-8", echo=False)
        return child

if __name__ == "__main__":
    config.tempdir = tempfile.mkdtemp()
    main()
