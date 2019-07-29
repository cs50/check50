import unittest
import os
import pathlib
import tempfile

import check50.py
import check50.internal

class Base(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

        self.filename = "foo.py"
        self.write("")

    def write(self, source):
        with open(self.filename, "w") as f:
            f.write(source)

    def tearDown(self):
        self.working_directory.cleanup()

    def runpy(self):
        self.process = check50.run(f"python3 ./{self.filename}")

class TestAppendCode(Base):
    def setUp(self):
        super().setUp()
        self.other_filename = "bar.py"
        with open(self.other_filename, "w") as f:
            f.write("baz")

    def test_empty_append(self):
        check50.py.append_code(self.filename, self.other_filename)
        with open(self.filename, "r") as f1, open(self.other_filename, "r") as f2:
            self.assertEqual(f1.read(), f"\n{f2.read()}")

    def test_append(self):
        with open(self.other_filename, "r") as f:
            old_content2 = f.read()

        self.write("qux")
        check50.py.append_code(self.filename, self.other_filename)
        with open(self.filename, "r") as f1, open(self.other_filename, "r") as f2:
            content1 = f1.read()
            content2 = f2.read()

        self.assertNotEqual(content1, content2)
        self.assertEqual(content2, old_content2)
        self.assertEqual(content1, "qux\nbaz")


class TestImport_(Base):
    def setUp(self):
        super().setUp()
        self._old_check_dir = check50.internal.check_dir
        os.mkdir("bar")
        with open("./bar/baz.py", "w") as f:
            f.write("qux = 0")
        check50.internal.check_dir = pathlib.Path(".").absolute()

    def tearDown(self):
        super().tearDown()
        check50.internal.check_dir = self._old_check_dir

    def test_simple_import(self):
        mod = check50.py.import_("foo.py")
        self.assertEqual(mod.__name__, "foo")

    def test_relative_import(self):
        mod = check50.py.import_("./bar/baz.py")
        self.assertEqual(mod.__name__, "baz")
        self.assertEqual(mod.qux, 0)


if __name__ == "__main__":
    unittest.main()
