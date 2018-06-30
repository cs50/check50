import unittest
import os
import yaml
import pathlib
import check50
import check50.simple
import tempfile

class Base(unittest.TestCase):

    config_file = ".check50.yaml"

    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()

    def write(self, source):
        with open(self.config_file, "w") as f:
            f.write(source)

class TestCompile(Base):
    def test_one_complete_check(self):
        checks = yaml.safe_load(\
"""checks:
  bar:
    - run: python3 foo.py
      stdin: baz
      stdout: baz
      exit: 0
""")["checks"]

        expectation = \
"""import check50

@check50.check()
def bar():
    \"\"\"bar\"\"\"
    check50.run("python3 foo.py").stdin("baz", prompt=False).stdout("baz", regex=False).exit(0)"""

        result = check50.simple.compile(checks)
        self.assertEqual(result, expectation)

    def test_multiple_checks(self):
        checks = yaml.safe_load(\
"""checks:
  bar:
    - run: python3 foo.py
      exit: 0
  baz:
    - run: python3 foo.py
      exit: 0
""")["checks"]

        expectation = \
"""import check50

@check50.check()
def bar():
    \"\"\"bar\"\"\"
    check50.run("python3 foo.py").exit(0)

@check50.check()
def baz():
    \"\"\"baz\"\"\"
    check50.run("python3 foo.py").exit(0)"""

        result = check50.simple.compile(checks)
        self.assertEqual(result, expectation)

    def test_multi(self):
        checks = yaml.safe_load(\
"""checks:
  bar:
    - run: python3 foo.py
      stdin:
        - foo
        - bar
      stdout:
        - baz
        - qux
      exit: 0
""")["checks"]

        expectation = \
"""import check50

@check50.check()
def bar():
    \"\"\"bar\"\"\"
    check50.run("python3 foo.py").stdin("foo\\nbar", prompt=False).stdout("baz\\nqux", regex=False).exit(0)"""

        result = check50.simple.compile(checks)
        self.assertEqual(result, expectation)

    def test_multiline(self):
        checks = yaml.safe_load(\
"""checks:
  bar:
    - run: python3 foo.py
      stdout: |
        Hello
        World!
      exit: 0
""")["checks"]

        expectation = \
"""import check50

@check50.check()
def bar():
    \"\"\"bar\"\"\"
    check50.run("python3 foo.py").stdout("Hello\\nWorld!\\n", regex=False).exit(0)"""

        result = check50.simple.compile(checks)
        self.assertEqual(result, expectation)

    def test_number_in_name(self):
        checks = yaml.safe_load(\
"""checks:
  0bar:
    - run: python3 foo.py
""")["checks"]

        result = check50.simple.compile(checks)
        self.assertTrue("def _0bar" in result)
        self.assertTrue("\"\"\"0bar\"\"\"" in result)

    def test_space_in_name(self):
        checks = yaml.safe_load(\
"""checks:
  bar baz:
    - run: python3 foo.py
""")["checks"]

        result = check50.simple.compile(checks)
        self.assertTrue("def bar_baz" in result)
        self.assertTrue("\"\"\"bar baz\"\"\"" in result)

    def test_dash_in_name(self):
        checks = yaml.safe_load(\
"""checks:
  bar-baz:
    - run: python3 foo.py
""")["checks"]

        result = check50.simple.compile(checks)
        self.assertTrue("def bar_baz" in result)
        self.assertTrue("\"\"\"bar-baz\"\"\"" in result)

    def test_missing_exit(self):
        checks = yaml.safe_load(\
"""checks:
  bar:
    - run: python3 foo.py
""")["checks"]

        result = check50.simple.compile(checks)
        self.assertTrue(".exit()" in result)


if __name__ == "__main__":
    unittest.main()
