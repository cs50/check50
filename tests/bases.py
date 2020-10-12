import contextlib
import os
import shutil
import tempfile
import unittest

import pexpect

import check50
import check50.internal


class Base(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()


class CBase(Base):
    CLANG_INSTALLED = bool(shutil.which("clang"))
    VALGRIND_INSTALLED = bool(shutil.which("valgrind"))

    def setUp(self):
        super().setUp()
        if not self.CLANG_INSTALLED:
            raise unittest.SkipTest("clang not installed")
        if not self.VALGRIND_INSTALLED:
            raise unittest.SkipTest("valgrind not installed")


class FlaskBase(Base):
    try:
        import flask
        FLASK_INSTALLED = True
    except ModuleNotFoundError:
        FLASK_INSTALLED = False

    def setUp(self):
        super().setUp()
        if not self.FLASK_INSTALLED:
            raise unittest.SkipTest("flask not installed")


class PythonBase(Base):
    def setUp(self):
        super().setUp()

        self.filename = "foo.py"
        self.write("")

        self.process = None

    def tearDown(self):
        super().tearDown()
        if self.process and self.process.process.isalive():
            self.process.kill()

    def write(self, source):
        with open(self.filename, "w") as f:
            f.write(source)

    def runpy(self):
        self.process = check50.run(f"python3 ./{self.filename}")


class SimpleBase(Base):
    compiled_loc = None

    def setUp(self):
        super().setUp()
        if os.path.exists(self.compiled_loc):
            os.remove(self.compiled_loc)

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.compiled_loc):
            os.remove(self.compiled_loc)


class SpawnBase(Base):
    @contextlib.contextmanager
    def spawn(self, cmd):
        process = pexpect.spawn(cmd)
        process.str_last_chars = 1000

        try:
            yield process
        except pexpect.exceptions.ExceptionPexpect as e:
            e.value += "\n process output in utf-8:\n" + process.before.decode("utf-8")
            raise e
