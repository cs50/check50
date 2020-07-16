import json
import os
import pexpect
import pathlib
import sys
import unittest

from bases import SpawnBase, SimpleBase

CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"


class TestExists(SpawnBase):
    def test_no_file(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exists") as process:
            process.expect_exact(":(")
            process.expect_exact("foo.py exists")
            process.expect_exact("foo.py not found")
            process.close(force=True)

    def test_with_file(self):
        open("foo.py", "w").close()
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exists") as process:
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.close(force=True)


class TestExitPy(SpawnBase):
    def test_no_file(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exit_py") as process:
            process.expect_exact(":(")
            process.expect_exact("foo.py exists")
            process.expect_exact("foo.py not found")
            process.expect_exact(":|")
            process.expect_exact("foo.py exits properly")
            process.expect_exact("can't check until a frown turns upside down")
            process.close(force=True)

    def test_with_correct_file(self):
        open("foo.py", "w").close()
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exit_py") as process:
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.expect_exact(":)")
            process.expect_exact("foo.py exits properly")
            process.close(force=True)

    def test_with_incorrect_file(self):
        with open("foo.py", "w") as f:
            f.write("from sys import exit\nexit(1)")

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/exit_py") as process:
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.expect_exact(":(")
            process.expect_exact("foo.py exits properly")
            process.expect_exact("expected exit code 0, not 1")
            process.close(force=True)


class TestStdoutPy(SpawnBase):
    def test_no_file(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py") as process:
            process.expect_exact(":(")
            process.expect_exact("foo.py exists")
            process.expect_exact("foo.py not found")
            process.expect_exact(":|")
            process.expect_exact("prints hello")
            process.expect_exact("can't check until a frown turns upside down")
            process.close(force=True)

    def test_with_empty_file(self):
        open("foo.py", "w").close()

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py") as process:
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.expect_exact(":(")
            process.expect_exact("prints hello")
            process.expect_exact("expected \"hello\", not \"\"")
            process.close(force=True)


    def test_with_correct_file(self):
        with open("foo.py", "w") as f:
            f.write('print("hello")')

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdout_py") as process:
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.expect_exact(":)")
            process.expect_exact("prints hello")
            process.close(force=True)


class TestStdinPy(SpawnBase):
    def test_no_file(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py") as process:
            process.expect_exact(":(")
            process.expect_exact("foo.py exists")
            process.expect_exact("foo.py not found")
            process.expect_exact(":|")
            process.expect_exact("prints hello name")
            process.expect_exact("can't check until a frown turns upside down")
            process.close(force=True)

    def test_with_empty_file(self):
        open("foo.py", "w").close()

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py") as process:
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.expect_exact(":(")
            process.expect_exact("prints hello name")
            process.expect_exact("expected \"hello bar\", not \"\"")
            process.close(force=True)

    def test_with_correct_file(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint("hello", name)')

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_py") as process:
            process.expect_exact(":)")
            process.expect_exact("foo.py exists")
            process.expect_exact(":)")
            process.expect_exact("prints hello name")
            process.close(force=True)


class TestStdinPromptPy(SpawnBase):
    def test_no_file(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py") as process:
            process.expect_exact(":(")
            process.expect_exact("prints hello name")
            process.close(force=True)

    def test_with_empty_file(self):
        open("foo.py", "w").close()
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py") as process:
            process.expect_exact(":(")
            process.expect_exact("prints hello name")
            process.expect_exact("expected prompt for input, found none")
            process.close(force=True)

    def test_with_incorrect_file(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint("hello", name)')

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py") as process:
            process.expect_exact(":(")
            process.expect_exact("prints hello name")
            process.expect_exact("expected prompt for input, found none")
            process.close(force=True)

    def test_with_correct_file(self):
        with open("foo.py", "w") as f:
            f.write('name = input("prompt")\nprint("hello", name)')

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_prompt_py") as process:
            process.expect_exact(":)")
            process.expect_exact("prints hello name")
            process.close(force=True)


class TestStdinMultiline(SpawnBase):
    def test_no_file(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline") as process:
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

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline") as process:
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

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline") as process:
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

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/stdin_multiline") as process:
            process.expect_exact(":)")
            process.expect_exact("prints hello name (non chaining)")
            process.expect_exact(":)")
            process.expect_exact("prints hello name (non chaining) (prompt)")
            process.expect_exact(":)")
            process.expect_exact("prints hello name (chaining)")
            process.expect_exact(":)")
            process.expect_exact("prints hello name (chaining) (order)")
            process.close(force=True)


class TestCompileExit(SimpleBase, SpawnBase):
    compiled_loc = CHECKS_DIRECTORY / "compile_exit" / "__init__.py"

    def test_no_file(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_exit") as process:
            process.expect_exact(":(")
            process.expect_exact("exit")
            process.close(force=True)

    def test_with_correct_file(self):
        open("foo.py", "w").close()
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_exit") as process:
            process.expect_exact(":)")
            process.expect_exact("exit")
            process.close(force=True)


class TestCompileStd(SimpleBase, SpawnBase):
    compiled_loc = CHECKS_DIRECTORY / "compile_std" / "__init__.py"

    def test_no_file(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std") as process:
            process.expect_exact(":(")
            process.expect_exact("std")
            process.close(force=True)

    def test_with_incorrect_stdout(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint("hello", name)')

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std") as process:
            process.expect_exact(":)")
            process.expect_exact("std")
            process.close(force=True)

    def test_correct(self):
        with open("foo.py", "w") as f:
            f.write('name = input()\nprint(name)')

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_std") as process:
            process.expect_exact(":)")
            process.expect_exact("std")
            process.close(force=True)


class TestCompilePrompt(SimpleBase, SpawnBase):
    compiled_loc = CHECKS_DIRECTORY / "compile_prompt" / "__init__.py"

    def test_prompt_dev(self):
        with open("foo.py", "w"), open(self.compiled_loc, "w"):
            pass

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/compile_prompt") as process:
            process.expect_exact("check50 will compile the YAML checks to __init__.py")
            process.close(force=True)


class TestOutputModes(SpawnBase):
    def test_json_output(self):
        pexpect.run(f"check50 --dev -o json --output-file foo.json {CHECKS_DIRECTORY}/output")
        with open("foo.json", "r") as f:
            json_out = json.load(f)
            self.assertEqual(json_out["results"][0]["name"], "exists")

    def test_ansi_output(self):
        with self.spawn(f"check50 --dev -o ansi -- {CHECKS_DIRECTORY}/output") as process:
            process.expect_exact(":(")
            process.close(force=True)

    def test_html_output(self):
        with self.spawn(f"check50 --dev -o html -- {CHECKS_DIRECTORY}/output") as process:
            process.expect_exact("file://")
            process.close(force=True)

    def test_multiple_outputs(self):
        with self.spawn(f"check50 --dev -o html ansi -- {CHECKS_DIRECTORY}/output") as process:
            process.expect_exact("file://")
            process.expect_exact(":(")
            process.close(force=True)

    def test_default(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/output") as process:
            process.expect_exact(":(")
            process.expect_exact("file://")
            process.close(force=True)


class TestHiddenCheck(SpawnBase):
    def test_hidden_check(self):
        pexpect.run(f"check50 --dev -o json --output-file foo.json {CHECKS_DIRECTORY}/hidden")
        expected = [{'name': 'check', 'description': "check", 'passed': False, 'log': [], 'cause': {"rationale": "foo", "help": None}, 'data': {}, 'dependency': None}]
        with open("foo.json", "r") as f:
            self.assertEqual(json.load(f)["results"], expected)


class TestPayloadCheck(SpawnBase):
    def test_payload_check(self):
        pexpect.run(f"check50 --dev -o json --output-file foo.json {CHECKS_DIRECTORY}/payload")
        with open("foo.json", "r") as f:
            error = json.load(f)["error"]
        self.assertEqual(error["type"], "MissingFilesError")
        self.assertEqual(error["data"]["files"], ["missing.c"])
        self.assertEqual(pathlib.Path(error["data"]["dir"]).stem, pathlib.Path(self.working_directory.name).stem)


class TestTarget(SpawnBase):
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


class TestRemoteException(SpawnBase):
    def test_no_traceback(self):
        # Check that bar (part of traceback) is not shown
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/remote_exception_no_traceback") as process:
            self.assertRaises(pexpect.exceptions.EOF, lambda: process.expect("bar"))

        # Check that foo (the message) is shown
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/remote_exception_no_traceback") as process:
            process.expect("foo")

    def test_traceback(self):
        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/remote_exception_traceback") as process:
            process.expect("bar")
            process.expect("foo")


class TestInternalDirectories(SpawnBase):
    def test_directories_exist(self):
        with open("foo.py", "w") as f:
            f.write(os.getcwd())

        with self.spawn(f"check50 --dev {CHECKS_DIRECTORY}/internal_directories") as process:
            process.expect_exact(":)")

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(module=sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
