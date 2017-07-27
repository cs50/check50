import os
import sys

sys.path.append(os.getcwd())
from check50 import *

class Smile(Checks):

    @check()
    def exists(self):
        """smile exists."""
        super(Smile, self).exists("smile")
        self.include("../positive-words.txt")
        self.include("../negative-words.txt")

    @check("exists")
    def a_plus(self):
        """a+ returns :)"""
        self.spawn("./smile a+").stdout("^:)\n", ":)").exit()

    @check("exists")
    def love(self):
        """love returns :)"""
        self.spawn("./smile love").stdout("^:)\n",  ":)").exit()

    @check("exists")
    def zippy(self):
        """zippy returns :)"""
        self.spawn("./smile zippy").stdout("^:)\n", ":)").exit()

    @check("exists")
    def two_faced(self):
        """2-faced returns :("""
        self.spawn("./smile 2-faced").stdout("^:(\n", ":(").exit()

    @check("exists")
    def hate(self):
        """hate returns :("""
        self.spawn("./smile hate").stdout("^:(\n"), ":(").exit()

    @check("exists")
    def zombie(self):
        """zombie returns :("""
        self.spawn("./smile zombie").stdout("^:(\n"), ":(").exit()

    @check("exists")
    def jellyfish(self):
        """jellyfish returns :|"""
        self.spawn("./smile opinion").stdout("^:|\n", ":|").exit()

    @check("exists")
    def all_caps(self):
        """LOVE returns :)"""
        self.spawn("./smile LOVE").stdout("^:)\n").exit()

    @check("exists")
    def mixed_caps(self):
        """hAte returns :("""
        self.spawn("./smile hAte").stdout("^:(\n", ":(").exit()

    @check("exists")
    def ignore_comments(self):
        """ignores commented lines in word files"""
        self.spawn("./smile '; Opinion Lexicon: Positive'").stdout("^:(\n", ":|").exit()



