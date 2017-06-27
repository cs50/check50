import os
import re
import requests
import sys
import subprocess

sys.path.append(os.getcwd())
from check50 import *
from selenium import webdriver

class Sentiments(TestCase):

    ansi_escape = re.compile(r'\x1b[^m]*m')

    BASE_PATH = "http://127.0.0.1:5000"

    def server_up(self):
        env = {
            "FLASK_APP": "application.py"
        }

        self.server = self.spawn("flask run", env=env)
        self.driver = webdriver.PhantomJS()

    def server_down(self):
        self.driver.close()
        self.server.kill()

    def override_get_user_timeline(self):
        """Replaces student's get_user_timeline function with a deterministic one."""
        self.append_code("helpers.py", File("get_user_timeline.py"))

    @check()
    def exists_application(self):
        """application.py exists."""
        super(Sentiments, self).exists("application.py")

    @check()
    def exists_smile(self):
        """smile exists."""
        super(Sentiments, self).exists("smile")

    @check()
    def exists_tweets(self):
        """tweets exists."""
        super(Sentiments, self).exists("tweets")

    @check("exists_smile")
    def smile_love(self):
        """love returns :)"""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        out = self.spawn("./smile love").stdout()
        stripped = Sentiments.ansi_escape.sub('', out).rstrip()
        if (stripped != ":)"):
            raise Error("love did not return :)")

    @check("exists_smile")
    def smile_hate(self):
        """hate returns :("""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        out = self.spawn("./smile hate").stdout()
        stripped = Sentiments.ansi_escape.sub('', out).rstrip()
        if (stripped != ":("):
            raise Error("hate did not return :(")

    @check("exists_smile")
    def smile_jellyfish(self):
        """jellyfish returns :|"""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        out = self.spawn("./smile jellyfish").stdout()
        stripped = Sentiments.ansi_escape.sub('', out).rstrip()
        if (stripped != ":|"):
            raise Error("jellyfish did not return :|")

    @check("exists_smile")
    def smile_LOVE_caps(self):
        """LOVE returns :)"""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        out = self.spawn("./smile LOVE").stdout()
        stripped = Sentiments.ansi_escape.sub('', out).rstrip()
        if (stripped != ":)"):
            raise Error("LOVE did not return :)")

    @check("exists_smile")
    def smile_hAte_mixed(self):
        """hAte returns :("""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        out = self.spawn("./smile hAte").stdout()
        stripped = Sentiments.ansi_escape.sub('', out).rstrip()
        if (stripped != ":("):
            raise Error("hAte did not return :(")

    @check("exists_smile")
    def smile_no_args(self):
        """smile handles lack of arg"""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        self.spawn("./smile").exit(1)

    @check("exists_smile")
    def smile_too_many_args(self):
        """smile handles too many args"""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        self.spawn("./smile love hate").exit(1)



    @check("exists_tweets")
    def cs50_tweets(self):
        """cs50 tweets score correctly"""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        self.override_get_user_timeline()
        out = self.spawn("./tweets @cs50").stdout()
        stripped = Sentiments.ansi_escape.sub('', out).strip()
        if (stripped != "0 hello, world!"):
            raise Error("did not return as expected")

    @check("exists_tweets")
    def beatles(self):
        """beatles tweets score correctly"""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        self.override_get_user_timeline()
        tweets = self.spawn("./tweets @beatles").stdout().split("\n")
        beatles = ["1 All you need is love","-1 Hey Jude, don't make it bad", "0 Oh, I believe in yesterday"]
        count = 0
        while count < 3:
            stripped = Sentiments.ansi_escape.sub('', tweets[count]).strip()
            if (stripped != beatles[count]):
                raise Error("did not return {}").format(beatles[count])
            count += 1

    @check("exists_tweets")
    def elphiethedog(self):
        """elphiethedog tweets score correctly"""
        self.include("positive-words.txt")
        self.include("negative-words.txt")
        self.override_get_user_timeline()
        tweets = self.spawn("./tweets @elphiethedog").stdout().split("\n")
        elphiethedog = ["0 I love you but I hate your vacuum","1 The mailman seems friendly and fun to frighten"]
        count = 0
        while count < 2:
            stripped = Sentiments.ansi_escape.sub('', tweets[count]).strip()
            if (stripped != elphiethedog[count]):
                raise Error("did not return {}").format(elphiethedog[count])
            count += 1


    # @check("exists_tweets")
    # def tweets_no_args(self):
    #     """tweets handles lack of arg"""
    #     self.include("positive-words.txt")
    #     self.include("negative-words.txt")
    #     self.spawn("./tweets").exit(1)

    # @check("exists_tweets")
    # def tweets_too_many_args(self):
    #     """handles too many args"""
    #     self.include("positive-words.txt")
    #     self.include("negative-words.txt")
    #     self.spawn("./tweets love hate").exit(1)
