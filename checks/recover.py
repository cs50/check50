import os
import sys

sys.path.append(os.getcwd())
from check50 import File, TestCase, Error, check

class Recover(TestCase):

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

#     @check("exists")
#     def compiles(self):
#         """fifteen.c compiles."""
#         self.spawn("sed -i='' '/#include <unistd.h>/a \\\n#define usleep(x)' fifteen.c").exit(0)
#         self.include("fifteen/wrappers.c")
#         cflags = "-std=gnu99 -Wall -Werror -Wno-deprecated-declarations"
#         self.spawn("clang -S {} fifteen.c -o fifteen.S".format(cflags)).exit(0)
#         self.spawn("sed -i='' -e 's/callq\t_draw$/callq\t_cs50_draw/g' fifteen.S").exit(0)
#         self.spawn("sed -i='' -e 's/callq\tdraw$/callq\tcs50_draw/g' fifteen.S").exit(0)
#         # self.spawn("clang -fPIC -shared -o libwrapper.so wrappers.c")
#         self.spawn("clang {} -o fifteen wrappers.c fifteen.S -lcs50".format(cflags)).exit(0)
#
# # probably don't need this check -- we can just test the students work based on moves
#     @check("compiles")
#     def init3(self):
#         """init initializes 3x3 board correctly"""
#         self.spawn("true").exit(0)
#         child = self.spawn("./fifteen 3")
#         self.include("outputs/fifteen/init-3x3.txt")
#         child.child.expect("\x05\x00")
#         self.spawn("diff log.txt init-3x3.txt").stdout("", "").exit(0)
#
#     @check("compiles")
#     def invalid8(self):
#         """catches moving 8 as an illegal move for 3x3"""
#         child = self.spawn("./fifteen 3").stdin("8")
#         try:
#             child.child.expect('Illegal move.', timeout=3)
#         except pexpect.TIMEOUT:
#             raise Error()
#
#     @check("compiles")
#     def valid1(self):
#         """catches moving 1 as a legal move for 3x3"""
#         child = self.spawn("./fifteen 3").stdin("8")
#         try:
#             child.child.expect('Tile to move:', timeout=3)
#         except pexpect.TIMEOUT:
#             raise Error()
#
#     @check("compiles")
#     def move_up2(self):
#         """3x3 board, move blank up twice"""
#         child = self.spawn("./fifteen 3")
#         for move in ["3", "6"]:
#             child.stdin(move)
#             try:
#                 child.child.expect('Tile to move:', timeout=3)
#             except pexpect.TIMEOUT:
#                 raise Error()
#
#     @check("compiles")
#     def move_left2(self):
#         """3x3 board, move blank left twice"""
#         child = self.spawn("./fifteen 3")
#         # move_left2 = ["1", "2"]
#         for move in ["1", "2"]:
#             child.stdin(move)
#             try:
#                 child.child.expect('Tile to move:', timeout=3)
#             except pexpect.TIMEOUT:
#                 raise Error()
#
#     @check("compiles")
#     def move_left_right(self):
#         """3x3 board, move blank left then right"""
#         child = self.spawn("./fifteen 3")
#         for move in ["1", "1"]:
#             child.stdin(move)
#             try:
#                 child.child.expect('Tile to move:', timeout=3)
#             except pexpect.TIMEOUT:
#                 raise Error()
#
#     @check("compiles")
#     def move_up_down(self):
#         """3x3 board, move blank up then down"""
#         child = self.spawn("./fifteen 3")
#         for move in ["3", "3"]:
#             child.stdin(move)
#             try:
#                 child.child.expect('Tile to move:', timeout=3)
#             except pexpect.TIMEOUT:
#                 raise Error()
#
#     @check("compiles")
#     def move_around(self):
#         """3x3 board, move up-up-left-down-down-left-up-up-right-down-down-right"""
#         child = self.spawn("./fifteen 3")
#         for move in ["3", "6", "7", "4", "1", "2", "5", "8", "4", "1", "2", "3"]:
#             child.stdin(move)
#             try:
#                 child.child.expect('Tile to move:', timeout=3)
#             except pexpect.TIMEOUT:
#                 raise Error()
#
#     @check("compiles")
#     def invalid_start(self):
#         """3x3 board, from start try to move tile 2, 4, 5, 6, 7, 8"""
#         child = self.spawn("./fifteen 3")
#         for move in ["2", "4", "5", "6", "7", "8"]:
#             child.stdin(move)
#             try:
#                 child.child.expect('Illegal move.', timeout=3)
#             except pexpect.TIMEOUT:
#                 raise Error()
#
#     @check("compiles")
#     def invalid_center(self):
#         """3x3 board, move blank left (tile 1) then up (tile 4), then try to move tiles 1, 2, 6, 8"""
#         child = self.spawn("./fifteen 3")
#         for move in [ "2", "4"]:
#             child.stdin(move)
#             try:
#                 child.child.expect('Tile to move:', timeout=3)
#             except pexpect.TIMEOUT:
#                 raise Error()
#             for move in ["5", "6", "7", "8"]:
#                 child.stdin(move)
#             try:
#                 child.child.expect('Illegal move.', timeout=3)
#             except pexpect.TIMEOUT:
#                 raise Error()
