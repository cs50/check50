import os
import sys

sys.path.append(os.getcwd())
from check50 import *

class Resize_Less(TestCase):

    @check()
    def resize_bmp_exist(self):
        """resize.c and bmp.h exist."""
        super().exists("resize.c")
        super().exists("bmp.h")

    @check("resize_bmp_exist")
    def compiles(self):
        """resize.c compiles."""
        self.spawn("clang -o resize resize.c -lcs50").exit(0)

    @check("compiles")
    def scale_by_1(self):
        """doesn't resize 1x1-pixel BMP when n is 1"""
        self.include("1.bmp")
        child = self.spawn("./resize 1 1.bmp outfile.bmp")
        self.spawn("diff 1.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_by_2(self):
        """resizes 1x1-pixel BMP to 2x2 correctly when n is 2"""
        self.include("1.bmp")
        self.include("2.bmp")
        child = self.spawn("./resize 2 1.bmp outfile.bmp")
        self.spawn("diff 2.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_by_3(self):
        """resizes 1x1-pixel BMP to 3x3 correctly when n is 3"""
        self.include("1.bmp")
        self.include("3.bmp")
        child = self.spawn("./resize 3 1.bmp outfile.bmp")
        self.spawn("diff 3.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_by_4(self):
        """resizes 1x1-pixel BMP to 4x4 correctly when n is 4"""
        self.include("1.bmp")
        self.include("4.bmp")
        child = self.spawn("./resize 4 1.bmp outfile.bmp")
        self.spawn("diff 4.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_by_5(self):
        """resizes 1x1-pixel BMP to 5x5 correctly when n is 5"""
        self.include("1.bmp")
        self.include("5.bmp")
        child = self.spawn("./resize 5 1.bmp outfile.bmp")
        self.spawn("diff 5.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_2_to_4(self):
        """resizes 2x2-pixel BMP to 4x4 correctly when n is 2"""
        self.include("2.bmp")
        self.include("4.bmp")
        child = self.spawn("./resize 2 2.bmp outfile.bmp")
        self.spawn("diff 4.bmp outfile.bmp").stdout("", "").exit(0)
