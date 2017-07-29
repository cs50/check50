from check50 import *


@checks
class ResizeLess(Checks):
    hashes = {
        "1.bmp": "7762f5ed1684a1fb02d8dfd8e6fc248c00b8326d1d3c27df7a1c6a4f5ac278be",
        "2.bmp": "671254daeafeef77b9ce02819bea34f2e63d9e0ab6932c0b896adb2c24dc003e",
        "3.bmp": "8fedc60697f4a001cb489621d03051e8639f0a7ec6f0ec3b61014edb3271eacb",
        "4.bmp": "959b7760fd4fe12f29b4413c97ed7be33440caeb3253503b05b44dcd0afa641b",
        "5.bmp": "324931798c0de09c29957d790e0ef800a02a42274a5b147451137c042611bcd7",
        "6.bmp": "783123e79d8142b6d25518d6d43223d338f7aada6da9ecfd4bd29417d7b14e1e"
    }

    @check()
    def exists(self):
        """resize.c and bmp.h exist."""
        self.require("resize.c", "bmp.h")

    @check("exists")
    def compiles(self):
        """resize.c compiles."""
        self.spawn("clang -o resize resize.c -lcs50").exit(0)

    @check("compiles")
    def scale_by_1(self):
        """doesn't resize 1x1-pixel BMP when n is 1"""
        self.add("1.bmp")
        self.spawn("./resize 1 1.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["1.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_by_2(self):
        """resizes 1x1-pixel BMP to 2x2 correctly when n is 2"""
        self.add("1.bmp")
        self.spawn("./resize 2 1.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["2.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_by_3(self):
        """resizes 1x1-pixel BMP to 3x3 correctly when n is 3"""
        self.add("1.bmp")
        self.spawn("./resize 3 1.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["3.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_by_4(self):
        """resizes 1x1-pixel BMP to 4x4 correctly when n is 4"""
        self.add("1.bmp")
        self.spawn("./resize 4 1.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["4.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_by_5(self):
        """resizes 1x1-pixel BMP to 5x5 correctly when n is 5"""
        self.add("1.bmp")
        self.spawn("./resize 5 1.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["5.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_2_to_4(self):
        """resizes 2x2-pixel BMP to 4x4 correctly when n is 2"""
        self.add("2.bmp")
        self.spawn("./resize 2 2.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["4.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_3_to_6(self):
        """resizes 3x3-pixel BMP to 6x6 correctly when n is 2"""
        self.add("3.bmp")
        self.spawn("./resize 2 3.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["6.bmp"]:
            raise Error("resized image does not match expected image")

    @check("compiles")
    def scale_2_to_6(self):
        """resizes 2x2-pixel BMP to 6x6 correctly when n is 3"""
        self.add("2.bmp")
        self.spawn("./resize 3 2.bmp outfile.bmp").exit(0)
        if self.hash("outfile.bmp") != self.hashes["6.bmp"]:
            raise Error("resized image does not match expected image")
