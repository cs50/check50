import unittest
import json
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


# class TestExists(Base):
    # def test_no_file(self):
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exists")
        # process.expect_exact(":(")
        # process.expect_exact("foo.py exists")
        # process.expect_exact("foo.py not found")
        # process.close(force=True)

    # def test_with_file(self):
        # open("foo.py", "w").close()
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exists")
        # process.expect_exact(":)")
        # process.expect_exact("foo.py exists")
        # process.close(force=True)


# class TestExitPy(Base):
    # def test_no_file(self):
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exit_py")
        # process.expect_exact(":(")
        # process.expect_exact("foo.py exists")
        # process.expect_exact("foo.py not found")
        # process.expect_exact(":|")
        # process.expect_exact("foo.py exits properly")
        # process.expect_exact("can't check until a frown turns upside down")
        # process.close(force=True)

    # def test_with_file(self):
        # open("foo.py", "w").close()
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exit_py")
        # process.expect_exact(":)")
        # process.expect_exact("foo.py exists")
        # process.expect_exact(":)")
        # process.expect_exact("foo.py exits properly")
        # process.close(force=True)


# class TestStdoutPy(Base):
    # def test_no_file(self):
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py")
        # process.expect_exact(":(")
        # process.expect_exact("foo.py exists")
        # process.expect_exact("foo.py not found")
        # process.expect_exact(":|")
        # process.expect_exact("prints hello")
        # process.expect_exact("can't check until a frown turns upside down")
        # process.close(force=True)

    # def test_with_empty_file(self):
        # open("foo.py", "w").close()

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py")
        # process.expect_exact(":)")
        # process.expect_exact("foo.py exists")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello")
        # process.expect_exact("expected \"hello\", not \"\"")
        # process.close(force=True)


    # def test_with_correct_file(self):
        # with open("foo.py", "w") as f:
            # f.write('print("hello")')

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py")
        # process.expect_exact(":)")
        # process.expect_exact("foo.py exists")
        # process.expect_exact(":)")
        # process.expect_exact("prints hello")
        # process.close(force=True)


# class TestStdinPy(Base):
    # def test_no_file(self):
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py")
        # process.expect_exact(":(")
        # process.expect_exact("foo.py exists")
        # process.expect_exact("foo.py not found")
        # process.expect_exact(":|")
        # process.expect_exact("prints hello name")
        # process.expect_exact("can't check until a frown turns upside down")
        # process.close(force=True)

    # def test_with_empty_file(self):
        # open("foo.py", "w").close()

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py")
        # process.expect_exact(":)")
        # process.expect_exact("foo.py exists")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name")
        # process.expect_exact("expected \"hello bar\", not \"\"")
        # process.close(force=True)

    # def test_with_correct_file(self):
        # with open("foo.py", "w") as f:
            # f.write('name = input()\nprint("hello", name)')

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py")
        # process.expect_exact(":)")
        # process.expect_exact("foo.py exists")
        # process.expect_exact(":)")
        # process.expect_exact("prints hello name")
        # process.close(force=True)


# class TestStdinPromptPy(Base):
    # def test_no_file(self):
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name")
        # process.close(force=True)

    # def test_with_empty_file(self):
        # open("foo.py", "w").close()
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name")
        # process.expect_exact("expected prompt for input, found none")
        # process.close(force=True)

    # def test_with_incorrect_file(self):
        # with open("foo.py", "w") as f:
            # f.write('name = input()\nprint("hello", name)')

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name")
        # process.expect_exact("expected prompt for input, found none")
        # process.close(force=True)

    # def test_with_correct_file(self):
        # with open("foo.py", "w") as f:
            # f.write('name = input("prompt")\nprint("hello", name)')

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py")
        # process.expect_exact(":)")
        # process.expect_exact("prints hello name")
        # process.close(force=True)


# class TestStdinMultiline(Base):
    # def test_no_file(self):
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (non chaining)")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (non chaining) (prompt)")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (chaining)")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (chaining) (order)")
        # process.close(force=True)

    # def test_with_empty_file(self):
        # open("foo.py", "w").close()

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (non chaining)")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (non chaining) (prompt)")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (chaining)")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (chaining) (order)")
        # process.close(force=True)

    # def test_with_incorrect_file(self):
        # with open("foo.py", "w") as f:
            # f.write('name = input()\nprint("hello", name)')

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (non chaining)")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (non chaining) (prompt)")
        # process.expect_exact("expected prompt for input, found none")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (chaining)")
        # process.expect_exact(":(")
        # process.expect_exact("prints hello name (chaining) (order)")
        # process.close(force=True)

    # def test_with_correct_file(self):
        # with open("foo.py", "w") as f:
            # f.write('for _ in range(2):\n    name = input("prompt")\n    print("hello", name)')

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline")
        # process.expect_exact(":)")
        # process.expect_exact("prints hello name (non chaining)")
        # process.expect_exact(":)")
        # process.expect_exact("prints hello name (non chaining) (prompt)")
        # process.expect_exact(":)")
        # process.expect_exact("prints hello name (chaining)")
        # process.expect_exact(":)")
        # process.expect_exact("prints hello name (chaining) (order)")
        # process.close(force=True)


# class TestCompileExit(SimpleBase):
    # compiled_loc = CHECKS_DIRECTORY / "compile_exit" / "__init__.py"

    # def test_no_file(self):
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_exit")
        # process.expect_exact(":(")
        # process.expect_exact("exit")
        # process.close(force=True)

    # def test_with_correct_file(self):
        # open("foo.py", "w").close()
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_exit")
        # process.expect_exact(":)")
        # process.expect_exact("exit")
        # process.close(force=True)


# class TestCompileStd(SimpleBase):
    # compiled_loc = CHECKS_DIRECTORY / "compile_std" / "__init__.py"

    # def test_no_file(self):
        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std")
        # process.expect_exact(":(")
        # process.expect_exact("std")
        # process.close(force=True)

    # def test_with_incorrect_stdout(self):
        # with open("foo.py", "w") as f:
            # f.write('name = input()\nprint("hello", name)')

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std")
        # process.expect_exact(":)")
        # process.expect_exact("std")
        # process.close(force=True)

    # def test_correct(self):
        # with open("foo.py", "w") as f:
            # f.write('name = input()\nprint(name)')

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std")
        # process.expect_exact(":)")
        # process.expect_exact("std")
        # process.close(force=True)


# class TestCompilePrompt(SimpleBase):
    # compiled_loc = CHECKS_DIRECTORY / "compile_prompt" / "__init__.py"

    # def test_prompt_dev(self):
        # with open("foo.py", "w"), open(self.compiled_loc, "w"):
            # pass

        # process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_prompt")
        # process.expect_exact("check50 will compile the YAML checks to __init__.py")
        # process.close(force=True)


class TestHiddenCheck(Base):
    def test_hidden_check(self):
        pexpect.run(f"check50 --dev -o json --output-file foo.json {CHECKS_DIRECTORY}/hidden")
        expected = [{'name': 'check', 'description': None, 'passed': False, 'log': [], 'cause': {}, 'data': {}, 'dependency': None}]
        breakpoint()
        with open("foo.json", "r") as f:
            self.assertEqual(json.load(f)["results"], expected)

class TestPayloadCheck(Base):
    def test_payload_check(self):
        pexpect.run(f"check50 --dev -o json --output-file foo.json {CHECKS_DIRECTORY}/payload")
        with open("foo.json", "r") as f:
            error = json.load(f)["error"]
        self.assertEqual(error["type"], "MissingFilesError")
        self.assertEqual(error["data"]["files"], ["missing.c"])
        self.assertEqual(pathlib.Path(error["data"]["dir"]).stem, pathlib.Path(self.working_directory.name).stem)


if __name__ == "__main__":
    unittest.main()
