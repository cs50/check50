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

from bases import CBase

CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"



class TestCompile(CBase):
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

class TestValgrind(CBase):
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
    unittest.main()
