import unittest
import json
import pexpect
import pathlib
import shutil
import os
import tempfile
import subprocess

CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks/dynamic"

class Base(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()


class TestCreate(Base):
    def test_create_one(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/create_one")
        process.expect_exact(":) foo")
        process.expect_exact(":) bar")
        process.expect(pexpect.EOF)

    def test_collapsible_list(self):
        with open("answer.txt", "w") as f:
            f.write("wrong")

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/collapsible_list")
        process.expect_exact(":( foo")
        process.expect(pexpect.EOF)

        with open("answer.txt", "w") as f:
            f.write("correct")

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/collapsible_list")
        process.expect_exact(":) foo")
        process.expect_exact(":) bar")
        process.expect_exact(":) baz")
        process.expect(pexpect.EOF)

    def test_collapsible_list_on_failure(self):
        with open("answer.txt", "w") as f:
            f.write("wrong")

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/collapsible_list_on_failure")
        process.expect_exact(":( foo")
        process.expect_exact(":) bar")
        process.expect_exact(":) baz")
        process.expect(pexpect.EOF)

        with open("answer.txt", "w") as f:
            f.write("correct")

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/collapsible_list_on_failure")
        process.expect_exact(":) foo")
        process.expect(pexpect.EOF)

    def test_static_create_error(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/static_create_error")
        process.expect_exact("static check foo cannot create other checks, please mark it as dynamic with @check50.check(dynamic=True)")
        process.expect(pexpect.EOF)

    def test_circular_dependency(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/circular_dependency")
        process.expect_exact(":|")
        process.expect_exact("of check bar must be a check50 check itself")
        process.expect(pexpect.EOF)

    def test_register_twice(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/register_twice")
        process.expect_exact(":) foo")
        process.expect_exact(":) bar")
        process.expect(pexpect.EOF)


class TestUnittest(Base):
    def test_create_checks_from_unittest(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/python_unittest")
        process.expect_exact(":( some_tests.FooTest.test_fails passes")
        process.expect_exact(":) some_tests.FooTest.test_succeeds passes")
        process.expect(pexpect.EOF)


class TestPassState(Base):
    def test_pass_dynamic_state(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/pass_dynamic_state")
        process.expect_exact(":) foo")
        process.expect_exact(":) bar")
        process.expect(pexpect.EOF)

    def test_pass_dynamic_state_multiple(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/pass_dynamic_state_multiple")
        process.expect_exact(":) foo")
        process.expect_exact(":) bar")
        process.expect_exact(":) foo2")
        process.expect_exact(":) baz")
        process.expect_exact(":) bar2")
        process.expect(pexpect.EOF)

    def test_pass_static_state_to_dynamic(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/pass_static_state_to_dynamic")
        process.expect_exact(":) foo")
        process.expect_exact(":) bar")
        process.expect(pexpect.EOF)


class TestImport(Base):
    def test_import_checks_module_once(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/import_checks_module_once")
        process.expect_exact(":) foo")
        process.expect_exact(":) bar")
        process.expect(pexpect.EOF)

    def test_import_checks_module_twice(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/import_checks_module_twice")
        process.expect_exact(":) foo")
        process.expect_exact(":) bar")
        process.expect(pexpect.EOF)


if __name__ == "__main__":
    unittest.main()
