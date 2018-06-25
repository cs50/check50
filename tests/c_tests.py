import pexpect
import unittest
import sys
import shutil
import os
import functools
import tempfile
import pathlib
import check50
import check50.c
import check50.internal

CLANG_INSTALLED = bool(shutil.which("clang"))
VALGRIND_INSTALLED = bool(shutil.which("valgrind"))
CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"

class Base(unittest.TestCase):
    def setUp(self):
        if not CLANG_INSTALLED:
            raise unittest.SkipTest("clang not installed")
        if not VALGRIND_INSTALLED:
            raise unittest.SkipTest("valgrind not installed")

        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()

class TestCompile(Base):
    def test_compile_hello_world(self):
        with open("hello.c", "w") as f:
            src =   '#include <stdio.h>\n'\
                    'int main() {\n'\
                    '    printf("hello, world!\\n");\n'\
                    '}'
            f.write(src)

        check50.c.compile("hello.c")

        self.assertTrue(os.path.isfile("hello"))
        check50.run("./hello").stdout("hello, world!", regex=False)

class TestValgrind(Base):
    def setUp(self):
        super().setUp()
        if not (sys.platform == "linux" or sys.platform == "linux2"):
            raise unittest.SkipTest("skipping valgrind checks under anything other than Linux due to false positives")

    def test_no_leak(self):
        with open("foo.c", "w") as f:
            src = 'int main() {}'
            f.write(src)

        check50.c.compile("foo.c")
        with check50.internal.register:
            check50.c.valgrind("./foo").exit()

    def test_leak(self):
        with open("leak.c", "w") as f:
            src =   '#include <stdlib.h>\n'\
                    'void leak() {malloc(sizeof(int));}\n'\
                    'int main() {\n'\
                    '    leak();\n'\
                    '}'
            f.write(src)

        check50.c.compile("leak.c")
        with self.assertRaises(check50.Failure):
            with check50.internal.register:
                check50.c.valgrind("./leak").exit()


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(module=sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
