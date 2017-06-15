import os
import sys

sys.path.append(os.getcwd())
from check50 import File, Test, Error, check

class Vigenere(Test):

    @check()
    def exists(self):
        """vigenere.c exists."""
        super().exists("vigenere.c")

    @check("exists")
    def compiles(self):
        """vigenere.c compiles."""
        self.spawn("clang -o vigenere vigenere.c -lcs50").exit(0)

    @check("compiles")
    def test_aa(self):
        """encrypts "a" as "a" using "a" as keyword"""
        self.spawn("./vigenere a").stdin("a").stdout("ciphertext:\s*a\n", "ciphertext: a").exit(0)

    @check("compiles")
    def test_bazbarfoo(self):
        """encrypts "barfoo" as "caqgon" using "baz" as keyword"""
        self.spawn("./vigenere baz").stdin("barfoo").stdout("ciphertext:\s*caqgon\n", "ciphertext: caqgon").exit(0)

    @check("compiles")
    def test_mixedBaZBARFOO(self):
        """encrypts "BaRFoo" as "CaQGon" using "BaZ" as keyword"""
        self.spawn("./vigenere BaZ").stdin("BaRFoo").stdout("ciphertext:\s*CaQGon\n", "ciphertext: CaQGon").exit(0)

    @check("compiles")
    def test_allcapsBAZBARFOO(self):
        """encrypts "BARFOO" as "CAQGON" using "BAZ" as keyword"""
        self.spawn("./vigenere BAZ").stdin("BARFOO").stdout("ciphertext:\s*CAQGON\n", "ciphertext: CAQGON").exit(0)

    @check("compiles")
    def test_bazworld(self):
        """encrypts "world!$?" as "xoqmd!$?" using "baz" as keyword"""
        self.spawn("./vigenere baz").stdin("world!$?").stdout("ciphertext:\s*xoqmd!\$\?\n", "ciphertext: xoqmd!$?").exit(0)

    @check("compiles")
    def test_noarg(self):
        """handles lack of argv[1]"""
        self.spawn("./vigenere").exit(1)

    @check("compiles")
    def test_toomanyargs(self):
        """handles argc > 2"""
        self.spawn("./vigenere 1 2 3").exit(1)

    @check("compiles")
    def test_reject(self):
        """rejects "Hax0r2" as keyword"""
        self.spawn("./vigenere Hax0r2").exit(1)
