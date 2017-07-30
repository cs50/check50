from ..less import *

class ResizeMore(ResizeLess):

    @check("compiles")
    def scale_2_to_1(self):
        """resizes 2x2-pixel BMP to 1x1 correctly when f is 0.5"""
        self.add("2.bmp")
        self.spawn("./resize 0.5 2.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["1.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_4_to_2(self):
        """resizes 4x4-pixel BMP to 2x2 correctly when f is 0.5"""
        self.add("4.bmp")
        self.spawn("./resize 0.5 4.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["2.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_6_to_3(self):
        """resizes 6x6-pixel BMP to 3x3 correctly when f is 0.5"""
        self.add("6.bmp")
        self.spawn("./resize 0.5 6.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["3.bmp"]:
            raise Error("resized image does not match expected image")

