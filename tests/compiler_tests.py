import unittest
import os
import shutil
import yaml
import pathlib
import check50
import check50.compiler

WORKING_DIRECTORY = pathlib.Path(__file__).parent / f"temp_{__name__}"

class Base(unittest.TestCase):
    def setUp(self):
        os.mkdir(WORKING_DIRECTORY)
        os.chdir(WORKING_DIRECTORY)
        self.filename = ".check50.yaml"

    def tearDown(self):
        if os.path.isdir(WORKING_DIRECTORY):
            shutil.rmtree(WORKING_DIRECTORY)

    def write(self, source):
        with open(self.filename, "w") as f:
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
    check50.run("python3 foo.py").stdin("baz").stdout("baz", regex=False).exit(0)"""

        result = check50.compiler.compile(checks)
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

        result = check50.compiler.compile(checks)
        self.assertEqual(result, expectation)

    def test_multiline(self):
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
    check50.run("python3 foo.py").stdin("foo\\nbar").stdout("baz\\nqux", regex=False).exit(0)"""

        result = check50.compiler.compile(checks)
        self.assertEqual(result, expectation)

    def test_number_in_name(self):
        checks = yaml.safe_load(\
"""checks:
  0bar:
    - run: python3 foo.py
""")["checks"]

        result = check50.compiler.compile(checks)
        self.assertTrue("def _0bar" in result)
        self.assertTrue("\"\"\"0bar\"\"\"" in result)

    def test_space_in_name(self):
        checks = yaml.safe_load(\
"""checks:
  bar baz:
    - run: python3 foo.py
""")["checks"]

        result = check50.compiler.compile(checks)
        self.assertTrue("def bar_baz" in result)
        self.assertTrue("\"\"\"bar baz\"\"\"" in result)

    def test_dash_in_name(self):
        checks = yaml.safe_load(\
"""checks:
  bar-baz:
    - run: python3 foo.py
""")["checks"]

        result = check50.compiler.compile(checks)
        self.assertTrue("def bar_baz" in result)
        self.assertTrue("\"\"\"bar-baz\"\"\"" in result)

    def test_missing_exit(self):
        checks = yaml.safe_load(\
"""checks:
  bar:
    - run: python3 foo.py
""")["checks"]

        result = check50.compiler.compile(checks)
        self.assertTrue(".exit()" in result)
