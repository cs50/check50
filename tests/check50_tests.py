import unittest
import pexpect
import pathlib
import shutil
import os

WORKING_DIRECTORY = pathlib.Path(__file__).parent / f"temp_{__name__}"
CHECKS_DIRECTORY = pathlib.Path(__file__).parent / "checks"

class Base(unittest.TestCase):
    def setUp(self):
        os.mkdir(WORKING_DIRECTORY)
        os.chdir(WORKING_DIRECTORY)

    def tearDown(self):
        if os.path.isdir(WORKING_DIRECTORY):
            shutil.rmtree(WORKING_DIRECTORY)

class TestExists(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exists")
        process.expect_exact(":(")
        process.expect_exact("foo.py exists")
        process.expect_exact("foo.py not found")
        process.close(force=True)

    def test_with_file(self):
        with open("foo.py", "w") as f:
            pass

        try:
            process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exists")
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.close(force=True)
        finally:
            os.remove("foo.py")

class TestExitPy(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exit_py")
        process.expect_exact(":(")
        process.expect_exact("foo.py exists")
        process.expect_exact("foo.py not found")
        process.expect_exact(":|")
        process.expect_exact("foo.py exits properly")
        process.expect_exact("can't check until a frown turns upside down")
        process.close(force=True)

    def test_with_file(self):
        with open("foo.py", "w") as f:
            pass

        try:
            process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exit_py")
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.expect_exact(":)")
            process.expect_exact("foo.py exits properly")
            process.close(force=True)
        finally:
            os.remove("foo.py")
