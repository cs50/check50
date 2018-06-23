import unittest
import os
import pathlib
import shutil
import sys
import tempfile

import check50
import check50.api
import check50.internal


class Base(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

        self.filename = "foo.py"
        self.write("")

        self.process = None

    def tearDown(self):
        if self.process and self.process.process.isalive():
            self.process.kill()
        self.working_directory.cleanup()

    def write(self, source):
        with open(self.filename, "w") as f:
            f.write(source)

    def runpy(self):
        self.process = check50.run(f"python3 ./{self.filename}")

class TestInclude(Base):
    def setUp(self):
        super().setUp()
        self._old_check_dir = check50.internal.check_dir
        os.mkdir("bar")
        with open("./bar/baz.txt", "w") as f:
            pass
        check50.internal.check_dir = pathlib.Path("./bar").absolute()

    def tearDown(self):
        super().tearDown()
        check50.internal.check_dir = self._old_check_dir

    def test_include(self):
        check50.include("baz.txt")
        self.assertTrue((pathlib.Path(".").absolute() / "baz.txt").exists())
        self.assertTrue((check50.internal.check_dir / "baz.txt").exists())

class TestExists(Base):
    def test_file_does_not_exist(self):
        with self.assertRaises(check50.Failure):
            check50.exists("i_do_not_exist")

    def test_file_exists(self):
        check50.exists(self.filename)

class TestDiff(Base):
    def setUp(self):
        super().setUp()
        self.txt_filename = "foo.txt"
        with open(self.txt_filename, "w") as f:
            f.write("foo")

    def test_no_diff(self):
        self.write("foo")
        self.assertFalse(check50.diff(self.txt_filename, self.filename))

    def test_diff(self):
        self.write("bar")
        self.assertTrue(check50.diff(self.txt_filename, self.filename))

class TestImportChecks(Base):
    def setUp(self):
        super().setUp()
        self._old_check_dir = check50.internal.check_dir
        os.mkdir("bar")
        with open("./bar/baz.py", "w") as f:
            f.write("qux = 0")
        check50.internal.check_dir = pathlib.Path(".").absolute()

    def tearDown(self):
        super().tearDown()
        check50.internal.check_dir = self._old_check_dir

    def test_simple_import(self):
        mod = check50.import_checks("foo")
        self.assertEqual(mod.__name__, "foo")

    def test_relative_import(self):
        mod = check50.import_checks("./bar/baz")
        self.assertEqual(mod.__name__, "baz")
        self.assertEqual(mod.qux, 0)

class TestAppendCode(Base):
    def setUp(self):
        super().setUp()
        self.other_filename = "bar.py"
        with open(self.other_filename, "w") as f:
            f.write("baz")

    def test_empty_append(self):
        check50.append_code(self.filename, self.other_filename)
        with open(self.filename, "r") as f1, open(self.other_filename, "r") as f2:
            self.assertEqual(f1.read(), f"\n{f2.read()}")

    def test_append(self):
        with open(self.other_filename, "r") as f:
            old_content2 = f.read()

        self.write("qux")
        check50.append_code(self.filename, self.other_filename)
        with open(self.filename, "r") as f1, open(self.other_filename, "r") as f2:
            content1 = f1.read()
            content2 = f2.read()

        self.assertNotEqual(content1, content2)
        self.assertEqual(content2, old_content2)
        self.assertEqual(content1, "qux\nbaz")

class TestRun(Base):
    def test_returns_process(self):
        process = check50.run("python3 ./{self.filename}")
        self.assertIsInstance(process, check50.api.Process)

class TestProcessKill(Base):
    def test_kill(self):
        self.runpy()
        self.assertTrue(self.process.process.isalive())
        self.process.kill()
        self.assertFalse(self.process.process.isalive())

class TestProcessStdin(Base):
    def test_expect_prompt_no_prompt(self):
        self.write("x = input()")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdin("bar", prompt=True)

    def test_expect_prompt(self):
        self.write("x = input('foo')")
        self.runpy()
        self.process.stdin("bar", prompt=True)
        self.assertTrue(self.process.process.isalive())

    def test_no_prompt(self):
        self.write("x = input()\n")
        self.runpy()
        self.process.stdin("bar")
        self.assertTrue(self.process.process.isalive())

class TestProcessStdout(Base):
    def test_no_out(self):
        self.runpy()
        out = self.process.stdout(timeout=.1)
        self.assertEqual(out, "")
        self.assertFalse(self.process.process.isalive())

        self.write("print('foo')")
        self.runpy()
        out = self.process.stdout()
        self.assertEqual(out, "foo\n")
        self.assertFalse(self.process.process.isalive())

    def test_out(self):
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout("foo")
        self.assertFalse(self.process.process.isalive())

        self.write("print('foo')")
        self.runpy()
        self.process.stdout("foo\n")

    def test_outs(self):
        self.write("print('foo')\nprint('bar')\n")
        self.runpy()
        self.process.stdout("foo\n")
        self.process.stdout("bar")
        self.process.stdout("\n")
        self.assertTrue(self.process.process.isalive())

    def test_out_regex(self):
        self.write("print('foo')")
        self.runpy()
        self.process.stdout(".o.")
        self.process.stdout("\n")
        self.assertTrue(self.process.process.isalive())

    def test_out_no_regex(self):
        self.write("print('foo')")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(".o.", regex=False)
        self.assertFalse(self.process.process.isalive())

class TestProcessStdoutFile(Base):
    def setUp(self):
        super().setUp()
        self.txt_filename = "foo.txt"
        with open(self.txt_filename, "w") as f:
            f.write("foo")

    def test_file(self):
        self.write("print('bar')")
        self.runpy()
        with open(self.txt_filename, "r") as f:
            with self.assertRaises(check50.Failure):
                self.process.stdout(f, regex=False)

        self.write("print('foo')")
        self.runpy()
        with open(self.txt_filename, "r") as f:
            self.process.stdout(f, regex=False)

    def test_file_regex(self):
        self.write("print('bar')")
        with open(self.txt_filename, "w") as f:
            f.write(".a.")
        self.runpy()
        with open(self.txt_filename, "r") as f:
            self.process.stdout(f)

class TestProcessExit(Base):
    def test_exit(self):
        self.write("sys.exit(1)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.exit(0)
        self.process.kill()

        self.write("sys.exit(1)")
        self.runpy()
        self.process.exit(1)

    def test_no_exit(self):
        self.write("sys.exit(1)")
        self.runpy()
        exit_code = self.process.exit()
        self.assertEqual(exit_code, 1)

class TestProcessKill(Base):
    def test_kill(self):
        self.runpy()
        self.process.kill()
        self.assertFalse(self.process.process.isalive())

class TestProcessReject(Base):
    def test_reject(self):
        self.write("input()")
        self.runpy()
        self.process.reject()
        self.process.stdin("foo")
        with self.assertRaises(check50.Failure):
            self.process.reject()

    def test_no_reject(self):
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.reject()

if __name__ == '__main__':
    unittest.main()
