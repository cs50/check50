import unittest
import pexpect
import pathlib
import shutil
import os
import tempfile

CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"

class Base(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()

class TestExists(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exists")
        process.expect_exact(":(")
        process.expect_exact("foo.py exists")
        process.expect_exact("foo.py not found")
        process.close(force=True)

    def test_with_file(self):
        open("foo.py", "w").close()
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exists")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.close(force=True)

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
        open("foo.py", "w").close()
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exit_py")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.expect_exact(":)")
        process.expect_exact("foo.py exits properly")
        process.close(force=True)

class TestStdoutPy(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py")
        process.expect_exact(":(")
        process.expect_exact("foo.py exists")
        process.expect_exact("foo.py not found")
        process.expect_exact(":|")
        process.expect_exact("prints hello")
        process.expect_exact("can't check until a frown turns upside down")
        process.close(force=True)

    def test_with_empty_file(self):
        open("foo.py", "w").close()

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.expect_exact(":(")
        process.expect_exact("prints hello")
        process.expect_exact("expected \"hello\", not \"\"")
        process.close(force=True)


    def test_with_correct_file(self):
        with open("foo.py", "w") as f:
            f.write('print("hello")')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.expect_exact(":)")
        process.expect_exact("prints hello")
        process.close(force=True)

class TestStdinPy(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py")
        process.expect_exact(":(")
        process.expect_exact("foo.py exists")
        process.expect_exact("foo.py not found")
        process.expect_exact(":|")
        process.expect_exact("prints hello name")
        process.expect_exact("can't check until a frown turns upside down")
        process.close(force=True)

    def test_with_empty_file(self):
        open("foo.py", "w").close()

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.expect_exact(":(")
        process.expect_exact("prints hello name")
        process.expect_exact("expected \"hello bar\", not \"\"")
        process.close(force=True)

    def test_with_correct_file(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint("hello", name)')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.expect_exact(":)")
        process.expect_exact("prints hello name")
        process.close(force=True)

class TestStdinPromptPy(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py")
        process.expect_exact(":(")
        process.expect_exact("prints hello name")
        process.close(force=True)

    def test_with_empty_file(self):
        open("foo.py", "w").close()
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py")
        process.expect_exact(":(")
        process.expect_exact("prints hello name")
        process.expect_exact("expected prompt for input, found none")
        process.close(force=True)

    def test_with_incorrect_file(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint("hello", name)')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py")
        process.expect_exact(":(")
        process.expect_exact("prints hello name")
        process.expect_exact("expected prompt for input, found none")
        process.close(force=True)

    def test_with_correct_file(self):
        with open("foo.py", "w") as f:
            f.write('name = input("prompt")\nprint("hello", name)')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py")
        process.expect_exact(":)")
        process.expect_exact("prints hello name")
        process.close(force=True)

class TestStdinMultiline(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (non chaining)")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (non chaining) (prompt)")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (chaining)")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (chaining) (order)")
        process.close(force=True)

    def test_with_empty_file(self):
        open("foo.py", "w").close()

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (non chaining)")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (non chaining) (prompt)")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (chaining)")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (chaining) (order)")
        process.close(force=True)

    def test_with_incorrect_file(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint("hello", name)')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (non chaining)")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (non chaining) (prompt)")
        process.expect_exact("expected prompt for input, found none")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (chaining)")
        process.expect_exact(":(")
        process.expect_exact("prints hello name (chaining) (order)")
        process.close(force=True)

    def test_with_correct_file(self):
        with open("foo.py", "w") as f:
            f.write('for _ in range(2):\n    name = input("prompt")\n    print("hello", name)')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline")
        process.expect_exact(":)")
        process.expect_exact("prints hello name (non chaining)")
        process.expect_exact(":)")
        process.expect_exact("prints hello name (non chaining) (prompt)")
        process.expect_exact(":)")
        process.expect_exact("prints hello name (chaining)")
        process.expect_exact(":)")
        process.expect_exact("prints hello name (chaining) (order)")
        process.close(force=True)

class TestCompileExit(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_exit")
        process.expect_exact(":(")
        process.expect_exact("exit")
        process.close(force=True)

    def test_with_correct_file(self):
        open("foo.py", "w").close()
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_exit")
        process.expect_exact(":)")
        process.expect_exact("exit")
        process.close(force=True)

class TestCompileStd(Base):
    def test_no_file(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std")
        process.expect_exact(":(")
        process.expect_exact("std")
        process.close(force=True)

    def test_with_incorrect_stdout(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint("hello", name)')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std")
        process.expect_exact(":)")
        process.expect_exact("std")
        process.close(force=True)

    def test_correct(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint(name)')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std")
        process.expect_exact(":)")
        process.expect_exact("std")
        process.close(force=True)

if __name__ == "__main__":
    unittest.main()
