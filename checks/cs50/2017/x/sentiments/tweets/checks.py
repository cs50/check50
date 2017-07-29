import osimport re
import requests
import sys

sys.path.append(os.getcwd())
from check50 import *

class Tweets(Checks):

    @check()
    def exists(self):
        """tweets exists."""
        super(Tweets, self).exists("tweets")
        self.include("helpers.py")
        self.include("../positive-words.txt")
        self.include("../negative-words.txt")

    @check("exists")
    def cs50(self):
        """cs50 tweets score correctly"""
        self.spawn("./tweets @cs50").stdout("0 hello, world!").exit()

    @check("exists")
    def beatles(self):
        """beatles tweets score correctly"""
        self.spawn("./tweets @beatles").stdout("1 All you need is love")            \
                                       .stdout("-1 Hey Jude, don't make it bad")    \
                                       .stdout("0 Oh, I believe in yesterday")      \
                                       .exit()

    @check("exists")
    def elphiethedog(self):
        """elphiethedog tweets score correctly"""
        self.spawn("./tweets @elphiethedog").stdout("1 I love you but I hate your vaccuum")                 \
                                            .stdout("-1 The mailman seems friendly and fun to frighten")    \
                                            .exit()

    @check("exists")
    def subwords(self):
        """handles positive/negative words within other words"""
        self.spawn("./tweets @subwords").stdout("-1 The zealous zealot has zeal").exit()

    @check("exists")
    def captainkirk
