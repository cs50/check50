import unittest
import contextlib
import json
import pexpect
import pathlib
import shutil
import os
import tempfile

CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks/dynamic"

class Base(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()

    @contextlib.contextmanager
    def spawn(self, cmd):
        process = pexpect.spawn(cmd)
        process.str_last_chars = 1000

        try:
            yield process
        except pexpect.exceptions.ExceptionPexpect as e:
            e.value += "\n process output in utf-8:\n" + process.before.decode("utf-8")
            raise e


class TestOrder(Base):
    def test_display_order(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/display_order") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect_exact(":) baz")
            process.expect_exact(":) qux")
            process.expect(pexpect.EOF)

    def test_execution_order(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/execution_order") as process:
            process.expect_exact("1234")
            process.expect(pexpect.EOF)


class TestCreate(Base):
    def test_create_one(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/create_one") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect(pexpect.EOF)

    def test_collapsible_list(self):
        with open("answer.txt", "w") as f:
            f.write("wrong")

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/collapsible_list") as process:
            process.expect_exact(":( foo")
            process.expect(pexpect.EOF)

        with open("answer.txt", "w") as f:
            f.write("correct")

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/collapsible_list") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect_exact(":) baz")
            process.expect(pexpect.EOF)

    def test_collapsible_list_on_failure(self):
        with open("answer.txt", "w") as f:
            f.write("wrong")

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/collapsible_list_on_failure") as process:
            process.expect_exact(":( foo")
            process.expect_exact(":) bar")
            process.expect_exact(":) baz")
            process.expect(pexpect.EOF)

        with open("answer.txt", "w") as f:
            f.write("correct")

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/collapsible_list_on_failure") as process:
            process.expect_exact(":) foo")
            process.expect(pexpect.EOF)

    def test_static_create_error(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/static_create_error") as process:
            process.expect_exact("static check foo cannot create other checks, please mark it as dynamic with @check50.check(dynamic=True)")
            process.expect(pexpect.EOF)

    def test_circular_dependency(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/circular_dependency") as process:
            process.expect_exact(":|")
            process.expect_exact("of check bar must be a check50 check itself")
            process.expect(pexpect.EOF)

    def test_register_twice(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/register_twice") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect(pexpect.EOF)


class TestUnittest(Base):
    def test_create_checks_from_unittest(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/python_unittest") as process:
            process.expect_exact(":( some_tests.FooTest.test_fails passes")
            process.expect_exact(":) some_tests.FooTest.test_succeeds passes")
            process.expect(pexpect.EOF)


class TestPassState(Base):
    def test_pass_dynamic_state(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/pass_dynamic_state") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect(pexpect.EOF)

    def test_pass_dynamic_state_multiple(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/pass_dynamic_state_multiple") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect_exact(":) foo2")
            process.expect_exact(":) baz")
            process.expect_exact(":) bar2")
            process.expect(pexpect.EOF)

    def test_pass_static_state_to_dynamic(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/pass_static_state_to_dynamic") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect(pexpect.EOF)


class TestImport(Base):
    def test_import_checks_module_once(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/import_checks_module_once") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect(pexpect.EOF)

    def test_import_checks_module_twice(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/import_checks_module_twice") as process:
            process.expect_exact(":) foo")
            process.expect_exact(":) bar")
            process.expect(pexpect.EOF)


if __name__ == "__main__":
    unittest.main()
