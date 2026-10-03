import unittest
import os
import pathlib
import tempfile

import check50
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


class TestImportChecks(Base):
    def setUp(self):
        super().setUp()
        self._old_check_dir = check50.internal.check_dir
        os.mkdir("bar")
        check50.internal.check_dir = pathlib.Path(".").absolute()

    def tearDown(self):
        super().tearDown()
        check50.internal.check_dir = self._old_check_dir

    def test_simple_import(self):
        with open(".cs50.yaml", "w") as f:
            f.write("check50:\n")
            f.write("  checks: foo.py")
        mod = check50.import_checks(".")
        self.assertEqual(mod.__name__, pathlib.Path(self.working_directory.name).name)

    def test_relative_import(self):
        with open("./bar/baz.py", "w") as f:
            f.write("qux = 0")

        with open("./bar/.cs50.yaml", "w") as f:
            f.write("check50:\n")
            f.write("  checks: baz.py")

        mod = check50.import_checks("./bar")
        self.assertEqual(mod.__name__, "bar")
        self.assertEqual(mod.qux, 0)


class TestRun(Base):
    def test_returns_process(self):
        self.process = check50.run("python3 ./{self.filename}")


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
            self.process.stdin("bar")

    def test_expect_prompt(self):
        self.write("x = input('foo')")
        self.runpy()
        self.process.stdin("bar")
        self.assertTrue(self.process.process.isalive())

    def test_no_prompt(self):
        self.write("x = input()\n")
        self.runpy()
        self.process.stdin("bar", prompt=False)
        self.assertTrue(self.process.process.isalive())

class TestProcessStdout(Base):
    def test_no_out(self):
        self.runpy()
        out = self.process.stdout(timeout=1)
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

    def test_out_regex(self):
        self.write("print('foo')")
        self.runpy()
        self.process.stdout(".o.")
        self.process.stdout("\n")

    def test_out_no_regex(self):
        self.write("print('foo')")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(".o.", regex=False)
        self.assertFalse(self.process.process.isalive())

    def test_int(self):
        self.write("print(123)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(1)

        self.write("print(21)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(1)

        self.write("print(1.0)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(1)

        self.write("print('a1b')")
        self.runpy()
        self.process.stdout(1)

        self.write("print(1)")
        self.runpy()
        self.process.stdout(1)

    def test_float(self):
        self.write("print(1.01)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(1.0)

        self.write("print(21.0)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(1.0)

        self.write("print(1)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(1.0)

        self.write("print('a1.0b')")
        self.runpy()
        self.process.stdout(1.0)

        self.write("print(1.0)")
        self.runpy()
        self.process.stdout(1.0)

    def test_negative_number(self):
        self.write("print(1)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(-1)

        self.write("print(-1)")
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.stdout(1)

        self.write("print('2-1')")
        self.runpy()
        self.process.stdout(-1)

        self.write("print(-1)")
        self.runpy()
        self.process.stdout(-1)


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
        self.process.stdin("foo", prompt=False)
        with self.assertRaises(check50.Failure):
            self.process.reject()

    def test_no_reject(self):
        self.runpy()
        with self.assertRaises(check50.Failure):
            self.process.reject()

class TestMismatch(unittest.TestCase):
    """Test Mismatch exception class for proper JSON serialization."""
    
    def test_json_serialization_with_strings(self):
        """Test that regular strings are properly escaped for JSON."""
        import json
        
        test_cases = [
            # Regular strings
            ("hello", "world"),
            # Strings with quotes
            ('Hello "World"', 'Goodbye "World"'),
            # Strings with newlines
            ("First\nSecond", "First\nDifferent"),
            # Strings with backslashes
            ("Path\\to\\file", "Path\\to\\other"),
            # JSON-like strings
            ('{"key": "value"}', '{"key": "different"}'),
            # Mixed special characters
            ('Line with \\ and " and \n', 'Another \\ line " with \n'),
        ]
        
        for expected, actual in test_cases:
            with self.subTest(expected=expected, actual=actual):
                mismatch = check50.Mismatch(expected, actual)
                
                # Ensure payload can be serialized to JSON
                json_str = json.dumps(mismatch.payload)
                
                # Ensure it can be parsed back
                parsed = json.loads(json_str)
                
                # Verify expected fields are present
                self.assertIn('rationale', parsed)
                self.assertIn('expected', parsed)
                self.assertIn('actual', parsed)
                self.assertIsNone(parsed.get('help'))
    
    def test_json_serialization_with_special_values(self):
        """Test that special values like EOF and class types are handled."""
        import json
        from pexpect.exceptions import EOF, TIMEOUT
        
        test_cases = [
            # EOF and TIMEOUT constants
            (check50.EOF, "some output"),
            ("some input", check50.EOF),
            (check50.EOF, check50.EOF),
            # Class types (simulating the error case)
            (EOF, "output"),
            ("input", EOF),
            (EOF, TIMEOUT),
        ]
        
        for expected, actual in test_cases:
            with self.subTest(expected=expected, actual=actual):
                mismatch = check50.Mismatch(expected, actual)
                
                # Ensure payload can be serialized to JSON
                json_str = json.dumps(mismatch.payload)
                
                # Ensure it can be parsed back
                parsed = json.loads(json_str)
                
                # Verify expected fields are present and are strings
                self.assertIn('rationale', parsed)
                self.assertIn('expected', parsed)
                self.assertIn('actual', parsed)
                
                # Ensure values in payload are strings, not class types
                self.assertIsInstance(parsed['expected'], str)
                self.assertIsInstance(parsed['actual'], str)
    
    def test_mismatch_with_help(self):
        """Test that help messages are included in the payload."""
        import json
        
        mismatch = check50.Mismatch("expected", "actual", help="Did you forget something?")
        
        # Ensure payload can be serialized to JSON
        json_str = json.dumps(mismatch.payload)
        parsed = json.loads(json_str)
        
        # Verify help is in the payload
        self.assertEqual(parsed['help'], "Did you forget something?")
    
    def test_mismatch_with_truncation(self):
        """Test that long strings are truncated properly."""
        import json
        
        # Create very long strings that will be truncated
        long_expected = "a" * 1000
        long_actual = "b" * 1000
        
        mismatch = check50.Mismatch(long_expected, long_actual)
        
        # Ensure payload can be serialized to JSON
        json_str = json.dumps(mismatch.payload)
        parsed = json.loads(json_str)
        
        # Verify truncation occurred (should have ellipsis)
        self.assertIn("...", parsed['expected'])
        self.assertIn("...", parsed['actual'])

if __name__ == '__main__':
    unittest.main()
