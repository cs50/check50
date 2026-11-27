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


class TestImportChecksAssertionRewrite(Base):
    """
    Regression tests for https://github.com/cs50/check50/issues/393:
    checks pulled in via import_checks() must follow the same assertion rewriting rules
    as the main checks file.
    """

    def setUp(self):
        super().setUp()
        self._old_check_dir = check50.internal.check_dir
        self._old_assertion_rewrite = check50.internal.assertion_rewrite
        check50.internal.check_dir = pathlib.Path(".").absolute()
        check50.internal.assertion_rewrite = None

    def tearDown(self):
        super().tearDown()
        check50.internal.check_dir = self._old_check_dir
        check50.internal.assertion_rewrite = self._old_assertion_rewrite

    def write_checks(self, name, source):
        os.mkdir(name)
        with open(f"./{name}/.cs50.yaml", "w") as f:
            f.write("check50:\n")
            f.write("  checks: __init__.py")
        with open(f"./{name}/__init__.py", "w") as f:
            f.write(source)

    FLAG = "# ENABLE_CHECK50_ASSERT = 1\n"
    CHECK = (
        "def check():\n"
        "    actual = 'foo'\n"
        "    assert actual == 'bar'\n"
    )

    def test_flag_in_imported_file_rewrites(self):
        self.write_checks("less", self.FLAG + self.CHECK)
        mod = check50.import_checks("./less")
        with self.assertRaises(check50.Mismatch):
            mod.check()

    def test_no_flag_in_imported_file_does_not_rewrite(self):
        self.write_checks("less", self.CHECK)
        mod = check50.import_checks("./less")
        with self.assertRaises(AssertionError):
            mod.check()

    def test_rewrite_leaves_imported_file_untouched(self):
        self.write_checks("less", self.FLAG + self.CHECK)
        check50.import_checks("./less")
        with open("./less/__init__.py") as f:
            self.assertEqual(f.read(), self.FLAG + self.CHECK)

    def test_override_enabled_rewrites_without_flag(self):
        check50.internal.assertion_rewrite = True
        self.write_checks("less", self.CHECK)
        mod = check50.import_checks("./less")
        with self.assertRaises(check50.Mismatch):
            mod.check()

    def test_override_disabled_ignores_flag(self):
        check50.internal.assertion_rewrite = False
        self.write_checks("less", self.FLAG + self.CHECK)
        mod = check50.import_checks("./less")
        with self.assertRaises(AssertionError):
            mod.check()

    def test_nested_import_rewrites_each_file_by_its_own_flag(self):
        # more imports less; only less opts in to rewriting
        self.write_checks("less", self.FLAG + self.CHECK.replace("check", "less_check"))
        self.write_checks("more",
            "import check50\n"
            "less = check50.import_checks('./less')\n"
            "from less import *\n"
            + self.CHECK.replace("check", "more_check"))
        mod = check50.import_checks("./more")
        with self.assertRaises(check50.Mismatch):
            mod.less_check()
        with self.assertRaises(AssertionError):
            mod.more_check()


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
        """Test that long strings are truncated in the rationale but kept in the log."""
        # Longer than config.truncate_len (terminal) but shorter than
        # config.log_truncate_len (JSON/HTML log)
        long_expected = "a" * 1000
        long_actual = "b" * 1000

        mismatch = check50.Mismatch(long_expected, long_actual)

        # The terminal rationale is truncated
        self.assertIn("...", mismatch.payload['rationale'])
        self.assertLess(len(mismatch.payload['rationale']), 1000)

        # The log keeps the full strings, as plain text
        self.assertEqual(mismatch.payload['expected'], long_expected)
        self.assertEqual(mismatch.payload['actual'], long_actual)

    def test_mismatch_truncation_keeps_repr_intact(self):
        """Test that a truncated string is repr'd as a whole: balanced quotes, no split escapes."""
        from check50._api import _truncate

        # The first difference is far enough in that the snippet is centered around it
        n = check50.config.truncate_len * 4
        expected = "\n" * n
        actual = "\n" * (n - 1) + "x"

        mismatch = check50.Mismatch(expected, actual)
        rationale_expected, rationale_actual = mismatch.payload['rationale'].split("\n    actual:   ")
        rationale_expected = rationale_expected[len("expected: "):]

        for rendered, s, other in ((rationale_expected, expected, actual), (rationale_actual, actual, expected)):
            with self.subTest(rendered=rendered):
                # Truncate the plain string first, then repr the snippet
                self.assertEqual(rendered, repr(_truncate(s, other)))
                self.assertTrue(rendered.startswith("'") and rendered.endswith("'"))
                # Every backslash is followed by the "n" it escapes, so no escape was cut in half
                self.assertEqual(rendered.count("\\"), rendered.count("\\n"))

    def test_mismatch_non_string_inputs(self):
        """Test that only strings are quoted, so a number and its string form look different (#377)."""
        mismatch = check50.Mismatch(1, "1")

        self.assertEqual(mismatch.payload['rationale'], "expected: 1\n    actual:   '1'")
        # The log holds plain text for both
        self.assertEqual(mismatch.payload['expected'], "1")
        self.assertEqual(mismatch.payload['actual'], "1")

    def test_mismatch_with_list(self):
        """Test that a list is rendered as a list in the terminal and as lines in the log."""
        mismatch = check50.Mismatch(["a", "b"], "a\nc\n")

        self.assertEqual(mismatch.payload['rationale'], "expected: ['a', 'b']\n    actual:   'a\\nc\\n'")
        self.assertEqual(mismatch.payload['expected'], "a\nb")
        self.assertEqual(mismatch.payload['actual'], "a\nc\n")

    def test_mismatch_log_truncation(self):
        """Test that the log is still bounded by config.log_truncate_len."""
        length = check50.config.log_truncate_len + 1000
        long_expected = "a" * length
        long_actual = "b" * length

        mismatch = check50.Mismatch(long_expected, long_actual)

        self.assertIn("...", mismatch.payload['expected'])
        self.assertIn("...", mismatch.payload['actual'])
        self.assertLess(len(mismatch.payload['expected']), length)
        self.assertLess(len(mismatch.payload['actual']), length)

    def test_mismatch_preserves_sentinels(self):
        """Test that EOF and TIMEOUT are never truncated into their str() form."""
        from pexpect.exceptions import TIMEOUT

        mismatch = check50.Mismatch(check50.EOF, "x" * 100)
        self.assertEqual(mismatch.payload['expected'], "EOF")
        self.assertIn("expected: EOF", mismatch.payload['rationale'])

        mismatch = check50.Mismatch("x" * 100, TIMEOUT)
        self.assertEqual(mismatch.payload['actual'], "TIMEOUT")
        self.assertIn("actual:   TIMEOUT", mismatch.payload['rationale'])


class TestMissing(unittest.TestCase):
    """Test Missing exception class for truncation and JSON serialization."""

    def test_missing_with_truncation(self):
        """Test that a long collection is truncated in the rationale but kept in the log."""
        import json

        long_collection = "0\n" * 500

        missing = check50.Missing("hello world\n", long_collection)

        # The terminal rationale is truncated
        self.assertIn("...", str(missing))
        self.assertLess(len(str(missing)), len(long_collection))

        # The log keeps the full collection, as plain text with real newlines
        parsed = json.loads(json.dumps(missing.payload))
        self.assertEqual(parsed['missing_item'], "hello world\n")
        self.assertEqual(parsed['collection'], long_collection)

    def test_missing_log_truncation(self):
        """Test that the log is still bounded by config.log_truncate_len."""
        length = check50.config.log_truncate_len + 1000
        long_collection = "0" * length

        missing = check50.Missing("hello", long_collection)

        self.assertIn("...", missing.payload['collection'])
        self.assertLess(len(missing.payload['collection']), length)

    def test_missing_short_collection(self):
        """Test that a short collection is not truncated anywhere."""
        missing = check50.Missing("5", "1 2 3")

        self.assertEqual(str(missing), "Did not find '5' in '1 2 3'")
        self.assertEqual(missing.payload['missing_item'], "5")
        self.assertEqual(missing.payload['collection'], "1 2 3")

    def test_missing_with_eof(self):
        """Test that EOF as the missing item is rendered as the string EOF."""
        import json

        missing = check50.Missing(check50.EOF, "abc")

        self.assertEqual(str(missing), "Did not find EOF in 'abc'")
        parsed = json.loads(json.dumps(missing.payload))
        self.assertEqual(parsed['missing_item'], "EOF")
        self.assertEqual(parsed['collection'], "abc")

    def test_missing_with_list(self):
        """Test that a list collection reads as a list in the terminal and as lines in the log."""
        import json

        missing = check50.Missing("z", ["a", "b"])

        self.assertEqual(str(missing), "Did not find 'z' in ['a', 'b']")
        parsed = json.loads(json.dumps(missing.payload))
        self.assertEqual(parsed['collection'], "a\nb")

    def test_missing_non_string_inputs(self):
        """Test that only strings are quoted, so list items are not mistaken for strings (#377)."""
        missing = check50.Missing("1", [1, 2, 3])

        self.assertEqual(str(missing), "Did not find '1' in [1, 2, 3]")
        self.assertEqual(missing.payload['missing_item'], "1")
        self.assertEqual(missing.payload['collection'], "1\n2\n3")


class TestConfig(unittest.TestCase):
    """Test the truncation settings on check50.config."""

    def test_log_truncate_len_validation(self):
        original = check50.config.log_truncate_len
        try:
            check50.config.set_log_truncate_len(50)
            self.assertEqual(check50.config.log_truncate_len, 50)

            missing = check50.Missing("x", "0" * 200)
            self.assertIn("...", missing.payload['collection'])
            self.assertLess(len(missing.payload['collection']), 200)

            with self.assertRaises(ValueError):
                check50.config.set_log_truncate_len(0)
            with self.assertRaises(ValueError):
                check50.config.set_log_truncate_len("big")
        finally:
            check50.config.set_log_truncate_len(original)

if __name__ == '__main__':
    unittest.main()
