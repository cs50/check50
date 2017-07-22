import os
import sys

sys.path.append(os.getcwd())
from check50 import *
class Resize_More(TestCase):

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
        """doesn't resize 1x1-pixel BMP when f is 1.0"""
        self.include("outputs/resize/1.bmp")
        child = self.spawn("./resize 1.0 1.bmp outfile.bmp")
        self.spawn("diff 1.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_by_2(self):
        """resizes 1x1-pixel BMP to 2x2 correctly when f is 2.0"""
        self.include("outputs/resize/1.bmp")
        self.include("outputs/resize/2.bmp")
        child = self.spawn("./resize 2.0 1.bmp outfile.bmp")
        self.spawn("diff 2.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_by_3(self):
        """resizes 1x1-pixel BMP to 3x3 correctly when f is 3.0"""
        self.include("outputs/resize/1.bmp")
        self.include("outputs/resize/3.bmp")
        child = self.spawn("./resize 3.0 1.bmp outfile.bmp")
        self.spawn("diff 3.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_by_4(self):
        """resizes 1x1-pixel BMP to 4x4 correctly when f is 4.0"""
        self.include("outputs/resize/1.bmp")
        self.include("outputs/resize/4.bmp")
        child = self.spawn("./resize 4.0 1.bmp outfile.bmp")
        self.spawn("diff 4.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_by_5(self):
        """resizes 1x1-pixel BMP to 5x5 correctly when f is 5.0"""
        self.include("outputs/resize/1.bmp")
        self.include("outputs/resize/5.bmp")
        child = self.spawn("./resize 5.0 1.bmp outfile.bmp")
        self.spawn("diff 5.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_2_to_4(self):
        """resizes 2x2-pixel BMP to 4x4 correctly when f is 2.0"""
        self.include("outputs/resize/2.bmp")
        self.include("outputs/resize/4.bmp")
        child = self.spawn("./resize 2.0 2.bmp outfile.bmp")
        self.spawn("diff 4.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_2_to_1(self):
        """resizes 2x2-pixel BMP to 1x1 correctly when f is 0.5"""
        self.include("outputs/resize/2.bmp")
        self.include("outputs/resize/1.bmp")
        child = self.spawn("./resize 0.5 2.bmp outfile.bmp")
        self.spawn("diff 1.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_4_to_2(self):
        """resizes 4x4-pixel BMP to 2x2 correctly when f is 0.5"""
        self.include("outputs/resize/4.bmp")
        self.include("outputs/resize/2.bmp")
        child = self.spawn("./resize 0.5 4.bmp outfile.bmp")
        self.spawn("diff 2.bmp outfile.bmp").stdout("", "").exit(0)

    @check("compiles")
    def scale_6_to_3(self):
        """resizes 6x6-pixel BMP to 3x3 correctly when f is 0.5"""
        self.include("outputs/resize/6.bmp")
        self.include("outputs/resize/3.bmp")
        child = self.spawn("./resize 0.5 6.bmp outfile.bmp")
        self.spawn("diff 3.bmp outfile.bmp").stdout("", "").exit(0)
