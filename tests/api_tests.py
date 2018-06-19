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
    def test_noStdout(self):
        pass

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
