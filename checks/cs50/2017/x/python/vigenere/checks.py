import os
import sys

sys.path.append(os.getcwd())
from check50 import *

class Vigenere(Checks):

    @check()
    def exists(self):
        """vigenere.py exists."""
        super(Vigenere, self).exists("vigenere.py")

    @check("exists")
    def aa(self):
        """encrypts "a" as "a" using "a" as keyword"""
        self.spawn("python3 vigenere.py a").stdin("a").stdout("ciphertext:\s*a\n", "ciphertext: a").exit(0)

    @check("exists")
    def bazbarfoo_caqgon(self):
        """encrypts "barfoo" as "caqgon" using "baz" as keyword"""
        self.spawn("python3 vigenere.py baz").stdin("barfoo").stdout("ciphertext:\s*caqgon\n", "ciphertext: caqgon\n").exit(0)

    @check("exists")
    def mixedBaZBARFOO(self):
        """encrypts "BaRFoo" as "CaQGon" using "BaZ" as keyword"""
        self.spawn("python3 vigenere.py BaZ").stdin("BaRFoo").stdout("ciphertext:\s*CaQGon\n", "ciphertext: CaQGon\n").exit(0)

    @check("exists")
    def allcapsBAZBARFOO(self):
        """encrypts "BARFOO" as "CAQGON" using "BAZ" as keyword"""
        self.spawn("python3 vigenere.py BAZ").stdin("BARFOO").stdout("ciphertext:\s*CAQGON\n", "ciphertext: CAQGON\n").exit(0)

    @check("exists")
    def bazworld(self):
        """encrypts "world!$?" as "xoqmd!$?" using "baz" as keyword"""
        self.spawn("python3 vigenere.py baz").stdin("world!$?").stdout("ciphertext:\s*xoqmd!\$\?\n", "ciphertext: xoqmd!$?\n").exit(0)

    @check("exists")
    def noarg(self):
        """handles lack of argv[1]"""
        self.spawn("python3 vigenere.py").exit(1)

    @check("exists")
    def toomanyargs(self):
        """handles argc > 2"""
        self.spawn("python3 vigenere.py 1 2 3").exit(1)

    @check("exists")
    def reject(self):
        """rejects "Hax0r2" as keyword"""
        self.spawn("python3 vigenere.py Hax0r2").exit(1)
