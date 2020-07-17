import unittest
import pexpect
import pathlib

from bases import SpawnBase

CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks/dynamic"


class TestOrder(SpawnBase):
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


class TestCreate(SpawnBase):
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
            process.expect_exact("check with name bar is defined twice. Each check must have a unique name.")
            process.expect(pexpect.EOF)


class TestUnittest(SpawnBase):
    def test_create_checks_from_unittest(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/python_unittest") as process:
            process.expect_exact(":( some_tests.FooTest.test_fails passes")
            process.expect_exact(":) some_tests.FooTest.test_succeeds passes")
            process.expect(pexpect.EOF)


class TestPassState(SpawnBase):
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


class TestImport(SpawnBase):
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
