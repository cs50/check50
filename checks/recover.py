import os
import sys

sys.path.append(os.getcwd())
from check50 import File, Test, Error, check

class Recover(Test):

    @check()
    def exists(self):
        """recover.c exists."""
        super().exists("recover.c")

    @check("exists")
    def compiles(self):
        """recover.c compiles."""
        self.spawn("clang -o recover recover.c -lcs50 -lm").exit(0)


    @check("compiles")
    def test_noimage(self):
        """handles lack of forensic image"""
        self.spawn("./recover").exit(1)

    @check("compiles")
    def test_000(self):
        """init initializes 3x3 board correctly"""
        #self.spawn("./fifteen 3")
        import pexpect
        child = pexpect.spawn("./fifteen 3")
        child.expect(".+")
        import time
        print(os.getcwd(), file=sys.stderr)
        self.include("outputs/fifteen/init-3x3.txt")
        # child  = subprocess.Popen("./fifteen 3", shell=True)
        # time.sleep(3)
        # child.kill()
        subprocess.Popen("bash", shell=True).wait()

        # .stdin(None).exit(0)
        # subprocess.Popen("cat log.txt", shell = True).wait()
        self.spawn("diff log.txt init-3x3.txt").stdout("", "").exit(0)

    #
    # @check("compiles")
    # def test_secondamongthree(self):
    #     """finds 28 in {27,28,29}"""
    #     self.spawn("./find 28").stdin("27").stdin("28").stdin("29").stdin(None).exit(0)
    #
    # @check("compiles")
    # def test_thirdamongthree(self):
    #     """finds 28 in {26,27,28}"""
    #     self.spawn("./find 28").stdin("26").stdin("27").stdin("28").stdin(None).exit(0)
    #
    # @check("compiles")
    # def test_secondamongfour(self):
    #     """finds 28 in {27,28,29,30}"""
    #     self.spawn("./find 28").stdin("27").stdin("28").stdin("29").stdin("30").stdin(None).exit(0)
    #
    # @check("compiles")
    # def test_thirdamongfour(self):
    #     """finds 28 in {26,27,28,29}"""
    #     self.spawn("./find 28").stdin("26").stdin("27").stdin("28").stdin("29").stdin(None).exit(0)
    #
    # @check("compiles")
    # def test_fourthamongfour(self):
    #     """finds 28 in {25,26,27,28}"""
    #     self.spawn("./find 28").stdin("25").stdin("26").stdin("27").stdin("28").stdin(None).exit(0)
    #
    # @check("compiles")
    # def test_notamongthree(self):
    #     """doesn't find 28 in {25,26,27}"""
    #     self.spawn("./find 28").stdin("25").stdin("26").stdin("27").stdin(None).exit(1)
    #
    # @check("compiles")
    # def test_notamongfour(self):
    #     """doesn't find 28 in {25,26,27,29}"""
    #     self.spawn("./find 28").stdin("25").stdin("26").stdin("27").stdin("29").stdin(None).exit(1)
    #
    # @check("compiles")
    # def test_correctlysorts(self):
    #     """finds 28 in {30,27,28,26}"""
    #     self.spawn("./find 28").stdin("30").stdin("27").stdin("28").stdin("26").stdin(None).exit(0)
