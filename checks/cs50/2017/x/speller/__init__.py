from check50 import *


@checks
class Speller(Checks):

    @check()
    def exists(self):
        """dictionary.c, dictionary.h, and Makefile exist"""
        super(Speller, self).exists("dictionary.c")
        super(Speller, self).exists("dictionary.h")
        super(Speller, self).exists("Makefile")

    @check("exists")
    def compiles(self):
        """speller compiles"""
        self.include("speller.c")
        self.spawn("make").exit(0)

    @check("compiles")
    @valgrind
    def basic(self):
        """handles most basic words properly"""
        self.include("basic")
        self.spawn("./speller basic/dict basic/text").stdout(File("basic/out")).exit(0)

    @check("compiles")
    @valgrind
    def min_length(self):
        """handles min length (1-char) words"""
        self.include("min_length")
        self.spawn("./speller min_length/dict min_length/text").stdout(File("min_length/out")).exit(0)

    @check("compiles")
    @valgrind
    def max_length(self):
        """handles max length (45-char) words"""
        self.include("max_length")
        self.spawn("./speller max_length/dict max_length/text").stdout(File("max_length/out")).exit(0)

    @check("compiles")
    @valgrind
    def apostrophe(self):
        """handles words with apostrophes properly"""
        self.include("apostrophe")
        self.spawn("./speller apostrophe/without/dict apostrophe/with/text").stdout(File("apostrophe/outs/without-with")).exit(0)
        self.spawn("./speller apostrophe/with/dict apostrophe/without/text").stdout(File("apostrophe/outs/with-without")).exit(0)
        self.spawn("./speller apostrophe/with/dict apostrophe/with/text").stdout(File("apostrophe/outs/with-with")).exit(0)

    @check("compiles")
    @valgrind
    def case(self):
        """spell-checking is case-insensitive"""
        self.include("case")
        self.spawn("./speller case/dict case/text").stdout(File("case/out")).exit(0)

    @check("compiles")
    @valgrind
    def substring(self):
        """handles substrings properly"""
        self.include("substring")
        self.spawn("./speller substring/dict substring/text").stdout(File("substring/out")).exit(0)
