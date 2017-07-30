from check50 import *


class Fifteen(Checks):

    @check()
    def exists(self):
        """fifteen.c exists."""
        self.require("fifteen.c")

    @check("exists")
    def compiles(self):
        """fifteen.c compiles."""
        # Remove sleeps from student code
        self.spawn("sed -i='' '/#include <unistd.h>/a \\\n#define usleep(x)' fifteen.c").exit()

        cflags = "-std=c99 -Wall -Werror -Wno-deprecated-declarations"
        # Replace student's draw with our own
        self.add("simple_draw.c")
        self.spawn("clang -S {} fifteen.c -o fifteen.S".format(cflags)).exit(0)
        self.replace_fn("draw", "simple_draw", "fifteen.S")
        self.spawn("clang {} -o fifteen simple_draw.c fifteen.S -lcs50".format(cflags)).exit(0)

    @check("compiles")
    def init3(self):
        """3x3 board: init initializes board correctly"""
        self.spawn("./fifteen 3").stdout("8-7-6|5-4-3|2-1-0\n").stdout("Tile to move:")

    @check("init3")
    def invalid8(self):
        """3x3 board: catches moving 8 an illegal move"""
        self.spawn("./fifteen 3").stdin("8")                    \
                                 .stdout("Illegal move.")       \
                                 .stdout("8-7-6|5-4-3|2-1-0\n") \
                                 .stdout("Tile to move:")
    @check("init3")
    def valid1(self):
        """3x3 board: catches moving 1 as a legal move"""
        self.spawn("./fifteen 3").stdin("1")                    \
                                 .stdout("8-7-6|5-4-3|2-0-1\n") \
                                 .stdout("Tile to move:")

    @check("init3")
    def move_up2(self):
        """3x3 board: move blank up twice"""
        self.spawn("./fifteen 3").stdin("3")                    \
                                 .stdout("8-7-6|5-4-0|2-1-3\n") \
                                 .stdin("6")                    \
                                 .stdout("8-7-0|5-4-6|2-1-3\n")

    @check("init3")
    def move_left2(self):
        """3x3 board: move blank left twice"""
        self.spawn("./fifteen 3").stdin("1")                    \
                                 .stdout("8-7-6|5-4-3|2-0-1\n") \
                                 .stdin("2")                    \
                                 .stdout("8-7-6|5-4-3|0-2-1\n")

    @check("init3")
    def move_left_right(self):
        """3x3 board: move blank left then right"""
        self.spawn("./fifteen 3").stdin("1")                    \
                                 .stdout("8-7-6|5-4-3|2-0-1\n") \
                                 .stdin("2")                    \
                                 .stdout("8-7-6|5-4-3|2-1-0\n")

    @check("init3")
    def move_up_down(self):
        """3x3 board: move blank up then down"""
        self.spawn("./fifteen 3").stdin("3")                    \
                                 .stdout("8-7-6|5-4-0|2-1-3\n") \
                                 .stdin("3")                    \
                                 .stdout("8-7-6|5-4-3|2-1-0\n")

    @check("init3")
    def move_around(self):
        """3x3 board: move up-up-left-down-down-left-up-up-right-down-down-right"""
        child = self.spawn("./fifteen 3").stdout("Tile to move:")
        moves = ["3", "6", "7", "4", "1", "2", "5", "8", "4", "1", "2", "3"]
        for move in moves[:-1]:
            child.stdin(move).stdout("Tile to move:")
        child.stdin(moves[-1]).stdout("4-1-7|8-2-6|5-3-0")


    @check("init3")
    def invalid_start(self):
        """3x3 board: make sure none of 2, 4, 5, 6, 7, 8 move tile"""
        child = self.spawn("./fifteen 3").stdout("Tile to move:")
        moves = ["2", "4", "5", "6", "7", "8"]
        for move in moves:
            child.stdin(move)                   \
                 .stdout("Illegal move.")       \
                 .stdout("8-7-6|5-4-3|0-2-1\n") \
                 .stdout("Tile to move:")

    @check("init3")
    def invalid_center(self):
        """3x3 board: move blank left (tile 1) then up (tile 4), then try to move tiles 1, 2, 6, 8"""
        child = self.spawn("./fifteen 3").stdin("1")                    \
                                         .stdout("Tile to move:")       \
                                         .stdin("4")                    \
                                         .stdout("8-7-6|5-0-3|2-4-1")   \
                                         .stdout("Tile to move:")

        for move in ["1", "2", "6"]:
            child.stdin(move).stdout("Illegal move.")
        child.stdin("8").stdout("8-7-6|5-0-3|2-4-1")

    @check("init3")
    def win_3x3(self):
        """3x3 board: make sure game is winnable"""
        moves = "34125876412587641241235476123748648578564567865478"
        child = self.spawn("./fifteen 3").stdout("Tile to move:")
        for move in moves[:-1]:
            child.stdin(move).stdout("Tile to move:")
        child.stdin(moves[-1]).stdout("1-2-3|4-5-6|7-8-0\n").exit(0)

    @check("compiles")
    def win_4x4(self):
        """4x4 board: make sure game is winnable"""
        moves = [
            "4", "5", "6", "1", "2", "4", "5", "6", "1", "2",
            "3", "7", "11", "10", "9", "1", "2", "3", "4", "5",
            "6", "8", "1", "2", "3", "4", "7", "11", "10", "9",
            "14", "13", "12", "1", "2", "3", "4", "14", "13",
            "12", "1", "2", "3", "4", "14", "13", "12", "1",
            "2", "3", "4", "12", "9", "15", "1", "2", "3", "4",
            "12", "9", "13", "14", "9", "13", "14", "7", "5", "9",
            "13", "14", "15", "10", "11", "5", "9", "13", "7", "11",
            "5", "9", "13", "7", "11", "15", "10", "5", "9", "13", "15",
            "11", "8", "6", "7", "8", "14", "12", "6", "7", "8", "14",
            "12", "6", "7", "8", "14", "15", "11", "10", "6", "7", "8",
            "12", "15", "11", "10", "15", "11", "14", "12", "11", "15",
            "10", "14", "15", "11", "12"
        ]

        child = self.spawn("./fifteen 4").stdout("15-14-13-12|11-10-9-8|7-6-5-4|3-2-1-0\n") \
                                         .stdout("Tile to move:")
        for move in moves[:-1]:
            child.stdin(move).stdout("Tile to move:")
        child.stdin(moves[-1]).stdout("1-2-3-4|5-6-7-8|9-10-11-12|13-14-15-0").exit(0)
