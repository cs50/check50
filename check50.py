#!/usr/bin/env python3

import argparse
import importlib
import os
import pexpect
import traceback
import unittest

from termcolor import cprint

def main():

    # parse command line arguments
    parser = argparse.ArgumentParser(description="This is check50.")
    parser.add_argument("identifier", nargs=1)
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    identifier = args.identifier[0]
    files = args.files

    # import and run the checks
    checks = importlib.import_module("checks.{}".format(identifier))
    suite = checks.test_suite()
    results = TestResult()
    suite.run(results)

    # print the results
    print_results(results)

def print_results(results):
    for result in results.results:
        if result["status"] == TestResult.SUCCESS:
            cprint(":) {}".format(result["description"]), "green")
        elif result["status"] == TestResult.FAILURE:
            cprint(":( {}".format(result["description"]), "red")
            if result["error"] != None:
                cprint("    {}".format(result["error"]), "red")

class TestResult(unittest.TestResult):
    SUCCESS = 1
    FAILURE = 0
    INCOMPLETE = -1
    results = []
    
    def __init__(self):
        super().__init__(self)

    def addSuccess(self, test):
        self.results.append({
            "status": self.SUCCESS,
            "description": test.shortDescription()
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results.append({
            "status": self.FAILURE, 
            "description": test.shortDescription(),
            "error": test.rationale
        })

    def addError(self, test, err):
        super().addFailure(test, err)
        self.results.append({
            "status": self.FAILURE,
            "description": test.shortDescription(),
            "error": test.rationale
        })

    def addSkip(self, test, reason):
        super().addSkip(test, reason)

class Test(unittest.TestCase):

    def __init__(self, method_name):
        super().__init__(method_name)
        self.rationale = None

    def assert_compiles(self, msg="file must compile first"):
        self.rationale = msg
        self.assertTrue(Test.compiles)
        self.rationale = None

    def assert_exists(self, msg="file must exist first"):
        self.rationale = msg
        self.assertTrue(Test.exists)
        self.rationale = None

    def assert_matches(self, output, filename):
        correct = open(filename, "r").read()
        self.assertEqual(output, correct)
    
    def check_compiles(self, cmd):
        status, _ = self.execute(cmd)
        Test.compiles = status == 0
        self.assertTrue(Test.compiles)

    def check_exists(self, filename):
        Test.exists = os.path.isfile(filename)
        self.assertTrue(Test.exists)

    def check_reject(self, child, line):
        child.sendline(line)
        child.expect(".+")
        try:
            child.sendline("")
        except OSError:
            self.fail()

    def execute(self, cmd):
        child = pexpect.spawn(cmd, encoding="utf-8", echo=False)
        child.wait()
        return child.exitstatus, child.read()

    def output(self, child):
        return child.read().lstrip("\n").replace("\r\n", "\n")

    def spawn(self, cmd):
        child = pexpect.spawn(cmd, encoding="utf-8", echo=False)
        return child

if __name__ == "__main__":
    main()
