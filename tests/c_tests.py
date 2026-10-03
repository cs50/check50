import unittest
import sys
import shutil
import os
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
    def test_compile_incorrect(self):
        open("blank.c", "w").close()

        with self.assertRaises(check50.Failure):
            check50.c.compile("blank.c")

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

    def test_default_std_is_c23(self):
        # `bool`, `true` and `false` are keywords only in C23 (no <stdbool.h>),
        # so this source only compiles if the default -std is c23 or newer.
        with open("c23.c", "w") as f:
            f.write("int main(void) { bool ok = true; return ok ? 0 : 1; }\n")

        self.assertEqual(check50.c.CFLAGS["std"], "c23")
        check50.c.compile("c23.c")

        self.assertTrue(os.path.isfile("c23"))
        check50.run("./c23").exit(0)

        # Overriding the default std still works and is what the docs promise
        with self.assertRaises(check50.Failure):
            check50.c.compile("c23.c", exe_name="c23_c11", std="c11")

class TestValgrind(Base):
    def setUp(self):
        super().setUp()
        if not (sys.platform == "linux" or sys.platform == "linux2"):
            raise unittest.SkipTest("skipping valgrind checks under anything other than Linux due to false positives")

    def test_no_leak(self):
        check50.internal.check_running = True
        with open("foo.c", "w") as f:
            src = 'int main() {}'
            f.write(src)

        check50.c.compile("foo.c")
        with check50.internal.register:
            check50.c.valgrind("./foo").exit()
        check50.internal.check_running = False

    def test_leak(self):
        check50.internal.check_running = True
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
        check50.internal.check_running = False


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(module=sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
