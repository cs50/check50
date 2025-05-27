import pexpect
import unittest
import sys
import shutil
import os
import functools
import tempfile
import pathlib
import check50
import check50.c
import check50.internal

CLANG_INSTALLED = bool(shutil.which("clang"))
VALGRIND_INSTALLED = bool(shutil.which("valgrind"))
CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"

class Base(unittest.TestCase):
    starting_dir = os.getcwd()

    def setUp(self):
        if not CLANG_INSTALLED:
            raise unittest.SkipTest("clang not installed")

        # ensures each test starts from same cwd;
        # 'chdir' would otherwise persist between tests
        os.chdir(self.starting_dir)

        # write c test files to temp directory
        test_files = {}
        os.chdir("test_files")
        for file in os.listdir():
            with open(file) as f:
                test_files[file] = f.read()

        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

        for file in test_files:
            with open(file, "w") as f:
                f.write(test_files[file])

    def tearDown(self):
        self.working_directory.cleanup()

class TestCompile(Base):
    def test_compile_incorrect(self):
        with self.assertRaises(check50.Failure):
            check50.c.compile("blank.c")

    def test_compile_hello_world(self):
        check50.c.compile("hello.c")
        self.assertTrue(os.path.isfile("hello"))

class TestRun(Base):
    def test_stdout_hello_world(self):
        check50.c.compile("hello.c")
        check50.run("./hello").stdout("hello, world!", regex=False)

    def test_stdin_cash(self):
        check50.c.compile("cash.c", lcs50=True)
        check50.run("./cash").stdin("42", prompt=True).stdout("5").exit()

class TestValgrind(Base):
    def setUp(self):
        super().setUp()

        # valgrind installation check moved to here from Base()
        if not VALGRIND_INSTALLED:
            raise unittest.SkipTest("valgrind not installed")
        if not (sys.platform == "linux" or sys.platform == "linux2"):
            raise unittest.SkipTest("skipping valgrind checks under anything other than Linux due to false positives")

    def test_no_leak(self):
        check50.internal.check_running = True

        check50.c.compile("foo.c")
        with check50.internal.register:
            check50.c.valgrind("./foo").exit()
        check50.internal.check_running = False

    def test_leak(self):
        check50.internal.check_running = True

        check50.c.compile("leak.c")
        with self.assertRaises(check50.Failure):
            with check50.internal.register:
                check50.c.valgrind("./leak").exit()
        check50.internal.check_running = False


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(module=sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
