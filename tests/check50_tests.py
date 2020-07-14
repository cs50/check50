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

class TestStdoutTimeout(Base):
    def test_stdout_timeout(self):
        with open("foo.py", "w") as f:
            f.write("while True: pass")

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.expect_exact(":(")
        process.expect_exact("check50 waited 1 seconds for the output of the program")
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

class TestStdinHumanReadable(Base):
    def test_without_human_readable_string(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint("hello", name)')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.expect_exact("checking that foo.py exists...")
        process.expect_exact(":)")
        process.expect_exact("prints hello name")
        process.expect_exact("running python3 foo.py...")
        process.expect_exact("sending input bar...")
        process.expect_exact("checking for output \"hello bar\"...")
        process.close(force=True)

    def test_with_human_readable_string(self):
        with open("foo.py", "w") as f:
            f.write('name = input("prompt")')

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_human_readable_py")
        process.expect_exact(":)")
        process.expect_exact("foo.py exists")
        process.expect_exact("checking that foo.py exists...")
        process.expect_exact(":)")
        process.expect_exact("takes input")
        process.expect_exact("running python3 foo.py...")
        process.expect_exact("sending input bbb...")
        process.close(force=True)


class TestCompileExit(SimpleBase):
    compiled_loc = CHECKS_DIRECTORY / "compile_exit" / "__init__.py"

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


class TestCompileStd(SimpleBase):
    compiled_loc = CHECKS_DIRECTORY / "compile_std" / "__init__.py"

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


class TestCompilePrompt(SimpleBase):
    compiled_loc = CHECKS_DIRECTORY / "compile_prompt" / "__init__.py"

    def test_prompt_dev(self):
        with open("foo.py", "w"), open(self.compiled_loc, "w"):
            pass

        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_prompt")
        process.expect_exact("check50 will compile the YAML checks to __init__.py")
        process.close(force=True)


class TestOutputModes(Base):
    def test_json_output(self):
        pexpect.run(f"check50 --dev -o json --output-file foo.json {CHECKS_DIRECTORY}/output")
        with open("foo.json", "r") as f:
            json_out = json.load(f)
            self.assertEqual(json_out["results"][0]["name"], "exists")

    def test_ansi_output(self):
        process = pexpect.spawn(f"check50 --dev -o ansi -- {CHECKS_DIRECTORY}/output")
        process.expect_exact(":(")
        process.close(force=True)

    def test_html_output(self):
        process = pexpect.spawn(f"check50 --dev -o html -- {CHECKS_DIRECTORY}/output")
        process.expect_exact("file://")
        process.close(force=True)

    def test_multiple_outputs(self):
        process = pexpect.spawn(f"check50 --dev -o html ansi -- {CHECKS_DIRECTORY}/output")
        process.expect_exact("file://")
        process.expect_exact(":(")
        process.close(force=True)

    def test_default(self):
        process = pexpect.spawn(f"check50 --dev {CHECKS_DIRECTORY}/output")
        process.expect_exact(":(")
        process.expect_exact("file://")
        process.close(force=True)


class TestHiddenCheck(Base):
    def test_hidden_check(self):
        pexpect.run(f"check50 --dev -o json --output-file foo.json {CHECKS_DIRECTORY}/hidden")
        expected = [{'name': 'check', 'description': "check", 'passed': False, 'log': [], 'cause': {"rationale": "foo", "help": None}, 'data': {}, 'dependency': None}]
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


class TestTarget(Base):
    def test_target(self):
        open("foo.py", "w").close()

        pexpect.run(f"check50 --dev -o json --output-file foo.json --target exists1 -- {CHECKS_DIRECTORY}/target")
        with open("foo.json", "r") as f:
            output = json.load(f)

        self.assertEqual(len(output["results"]), 1)
        self.assertEqual(output["results"][0]["name"], "exists1")


    def test_target_with_dependency(self):
        open("foo.py", "w").close()

        pexpect.run(f"check50 --dev -o json --output-file foo.json --target exists3 -- {CHECKS_DIRECTORY}/target")
        with open("foo.json", "r") as f:
            output = json.load(f)

        self.assertEqual(len(output["results"]), 2)
        self.assertEqual(output["results"][0]["name"], "exists1")
        self.assertEqual(output["results"][1]["name"], "exists3")


    def test_two_targets(self):
        open("foo.py", "w").close()

        pexpect.run(f"check50 --dev -o json --output-file foo.json --target exists1 exists2 -- {CHECKS_DIRECTORY}/target")
        with open("foo.json", "r") as f:
            output = json.load(f)

        self.assertEqual(len(output["results"]), 2)
        self.assertEqual(output["results"][0]["name"], "exists1")
        self.assertEqual(output["results"][1]["name"], "exists2")


    def test_target_failing_dependency(self):
        open("foo.py", "w").close()

        pexpect.run(f"check50 --dev -o json --output-file foo.json --target exists5 -- {CHECKS_DIRECTORY}/target")
        with open("foo.json", "r") as f:
            output = json.load(f)

        self.assertEqual(len(output["results"]), 2)
        self.assertEqual(output["results"][0]["name"], "exists4")
        self.assertEqual(output["results"][1]["name"], "exists5")


if __name__ == "__main__":
    unittest.main()
