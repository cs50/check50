import os
import sys
import subprocess

sys.path.append(os.getcwd())
from check50 import File, TestCase, Error, check

class Speller(TestCase):

    @check()
    def dictionary_Makefile_exist(self):
        """dictionary.c, dictionary.h and Makefile exist"""
        super().exists("dictionary.c")
        super().exists("dictionary.h")
        super().exists("Makefile")

    @check("dictionary_Makefile_exist")
    def compiles(self):
        """speller compiles"""
        self.include("speller.c")
        self.spawn("make").exit(0)

    @check("compiles")
    def basic(self):
        """handles most basic words properly"""
        self.include("outputs/speller/basic")
        self.include("outputs/speller/basic.txt")
        self.spawn("./speller basic basic.txt").stdout(File("outputs/speller/basic.out")).exit(0)

    @check("compiles")
    def min_length(self):
        """handles min length (1-char) words"""
        self.include("outputs/speller/min_length")
        self.include("outputs/speller/min_length.txt")
        self.spawn("./speller min_length min_length.txt").stdout(File("outputs/speller/min_length.out")).exit(0)

    @check("compiles")
    def max_length(self):
        """handles max length (1-char) words"""
        self.include("outputs/speller/max_length")
        self.include("outputs/speller/max_length.txt")
        self.spawn("./speller max_length max_length.txt").stdout(File("outputs/speller/max_length.out")).exit(0)

    @check("compiles")
    def possessives(self):
        """handles possessives properly"""
        self.include("outputs/speller/foo")
        self.include("outputs/speller/foos")
        self.include("outputs/speller/foo.txt")
        self.include("outputs/speller/foos.txt")
        self.spawn("./speller foo foos.txt").stdout(File("outputs/speller/foo_foos.out")).exit(0)
        self.spawn("./speller foos foo.txt").stdout(File("outputs/speller/foos_foo.out")).exit(0)
        self.spawn("./speller foos foos.txt").stdout(File("outputs/speller/foos_foos.out")).exit(0)

    @check("compiles")
    def case_insensitivity(self):
        """spell-checking is case-insensitive"""
        self.include("outputs/speller/foo")
        self.include("outputs/speller/foo.txt")
        self.spawn("./speller foo foo.txt").stdout(File("outputs/speller/foo_foo.out")).exit(0)

    @check("compiles")
    def substring(self):
        """handles substrings properly"""
        self.include("outputs/speller/substring")
        self.include("outputs/speller/substring.txt")
        self.spawn("./speller substring substring.txt").stdout(File("outputs/speller/substring.out")).exit(0)
