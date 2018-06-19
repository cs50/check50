import unittest
import os
import shutil
import sys
import check50
import check50.api

class Base(unittest.TestCase):
    def setUp(self):
        self.filename = "dummy.py"
        self.write("")

    def tearDown(self):
        os.remove(self.filename)

    def write(self, source):
        with open(self.filename, "w") as f:
            f.write(source)

class TestExists(Base):
    def test_fileDoesNotExist(self):
        with self.assertRaises(check50.Failure):
            check50.exists("i_do_not_exist")

    def test_fileExists(self):
        check50.exists(self.filename)

class TestRun(Base):
    def test_returnsProcess(self):
        process = check50.run(f"python ./{self.filename}")
        self.assertIsInstance(process, check50.api.Process)
        process.kill()

class TestProcessKill(Base):
    def test_kill(self):
        process = check50.run(f"python ./{self.filename}")
        self.assertTrue(process.process.isalive())
        process.kill()
        self.assertFalse(process.process.isalive())

class TestProcessStdin(Base):
    def test_expectPrompt_noPrompt(self):
        self.write("x = input()")
        process = check50.run(f"python ./{self.filename}")
        with self.assertRaises(check50.Failure):
            process.stdin("bar")
        process.kill()

    def test_expectPrompt(self):
        self.write("x = input('foo')")
        process = check50.run(f"python ./{self.filename}")
        process.stdin("bar")
        self.assertTrue(process.process.isalive())
        process.kill()

    def test_noPrompt(self):
        self.write("x = input()\n")
        process = check50.run(f"python ./{self.filename}")
        process.stdin("bar", prompt=False)
        self.assertTrue(process.process.isalive())
        process.kill()

class TestProcessStdout(Base):
    def test_noOut(self):
        process = check50.run(f"python ./{self.filename}")
        out = process.stdout(timeout=.1)
        self.assertEqual(out, "")
        self.assertFalse(process.process.isalive())
        process.kill()

        self.write("print('foo')")
        process = check50.run(f"python ./{self.filename}")
        out = process.stdout()
        self.assertEqual(out, "foo\n")
        self.assertFalse(process.process.isalive())
        process.kill()

    def test_out(self):
        process = check50.run(f"python ./{self.filename}")
        with self.assertRaises(check50.Failure):
            process.stdout("foo")
        self.assertFalse(process.process.isalive())
        process.kill()

        self.write("print('foo')")
        process = check50.run(f"python ./{self.filename}")
        process.stdout("foo\n")
        self.assertTrue(process.process.isalive())
        process.kill()

    def test_outs(self):
        self.write("print('foo')\nprint('bar')\n")
        process = check50.run(f"python ./{self.filename}")
        process.stdout("foo\n")
        process.stdout("bar")
        process.stdout("\n")
        self.assertTrue(process.process.isalive())
        process.kill()

    def test_out_regex(self):
        self.write("print('foo')")
        process = check50.run(f"python ./{self.filename}")
        process.stdout(".o.")
        process.stdout("\n")
        self.assertTrue(process.process.isalive())
        process.kill()

class TestExit(Base):
    def test_exit(self):
        self.write("sys.exit(1)")
        process = check50.run(f"python ./{self.filename}")
        with self.assertRaises(check50.Failure):
            process.exit(0)
        process.kill()

        self.write("sys.exit(1)")
        process = check50.run(f"python ./{self.filename}")
        process.exit(1)
        process.kill()

if __name__ == '__main__':
    unittest.main()
