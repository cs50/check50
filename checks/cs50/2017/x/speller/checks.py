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
        self.include("basic")
        self.include("basic.txt")
        self.spawn("./speller basic basic.txt").stdout(File("basic.out")).exit(0)
    @check("compiles")
    def min_length(self):
        """handles min length (1-char) words"""
        self.include("min_length")
        self.include("min_length.txt")
        self.spawn("./speller min_length min_length.txt").stdout(File("min_length.out")).exit(0)

    @check("compiles")
    def max_length(self):
        """handles max length (1-char) words"""
        self.include("max_length")
        self.include("max_length.txt")
        self.spawn("./speller max_length max_length.txt").stdout(File("max_length.out")).exit(0)

    @check("compiles")
    def possessives(self):
        """handles possessives properly"""
        self.include("foo")
        self.include("foos")
        self.include("foo.txt")
        self.include("foos.txt")
        self.spawn("./speller foo foos.txt").stdout(File("foo_foos.out")).exit(0)
        self.spawn("./speller foos foo.txt").stdout(File("foos_foo.out")).exit(0)
        self.spawn("./speller foos foos.txt").stdout(File("foos_foos.out")).exit(0)

    @check("compiles")
    def case_insensitivity(self):
        """spell-checking is case-insensitive"""
        self.include("foo")
        self.include("foo.txt")
        self.spawn("./speller foo foo.txt").stdout(File("foo_foo.out")).exit(0)

    @check("compiles")
    def substring(self):
        """handles substrings properly"""
        self.include("substring")
        self.include("substring.txt")
        self.spawn("./speller substring substring.txt").stdout(File("substring.out")).exit(0)
