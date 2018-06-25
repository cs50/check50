import pexpect
import unittest
import sys
import os
import functools
import tempfile
import pathlib
import check50
import check50.c
import check50.internal

try:
    pexpect.spawn("which clang").expect_exact("clang")
    pexpect.spawn("which valgrind").expect_exact("valgrind")
    DEPENDENCIES_INSTALLED = True
except (pexpect.exceptions.EOF, pexpect.exceptions.ExceptionPexpect):
    DEPENDENCIES_INSTALLED = False

CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"

class Base(unittest.TestCase):
    def setUp(self):
        if not DEPENDENCIES_INSTALLED:
            raise unittest.SkipTest("clang and/or valgrind are not installed")

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

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(module=sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
