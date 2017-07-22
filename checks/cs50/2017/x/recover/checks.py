import os
import sys
import subprocess

sys.path.append(os.getcwd())
from check50 import *

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

    @check("compiles")
    def first_image(self):
        """recovers 000.jpg correctly"""
        self.include("card.raw")
        subprocess.call("bash", shell=True)
        self.spawn("./recover card.raw").exit(0)
        hash000 = 'c3ceda9dde5cf2212e96d6f61e2e849ac60e2c3cbdf0184f6e0c3b6ea5e69d31'
        if self.hash("000.jpg") != hash000:
            raise Error("recovered image does not match")

    @check("compiles")
    def middle_images(self):
        """recovers middle images correctly"""
        self.include("card.raw")
        self.spawn("./recover card.raw").exit(0)
        middlehashes = ['8c0bd07a6c232670fd55b50ac42611c349920a119ef575eb28f770b9c89753e4',
            '6a42aa4997a94d37d4087c26b705f876596999c426fedd0a927fd574b90cb760',
            '20b415907e05cc0e9b0ef2d9cbaac694578e01fa56967f578b2e6c9dc99f750d',
            '371c127d1654867dbd6f8ea21fee0eb0144054531ceb096999114badd1a5bb81',
            'f689bc482dd50a73fc91deff4a57db5425e3642cb38df198a63fa400ca1a4561',
            '17b6dd9483c7086abd14b37167e9f16d799c65df3ed734fb76c484c75622459a',
            '423bf36ff399e7aa805ff0690e130bdc90e992523eaf660c100baca27c06cfce',
            'f22fd0a4e18f076c043bd8306fe771f2fa843f764e5c9c399a8f61d4921c1743',
            '5933fbd4d2ce7194ed67241c1f65fc86b5c882884de63644ceef4cd6ec97dd4c',
            'cbf1f76713e3a0c6b2779f9a3489291783ee9e8f4ec7469d5be362e892cbfbdd',
            '24b2b88477534ee29f7370d0742c172bef083a8fa78505cbc4bf7fd7df3353ca',
            '2f1900342cfa54c0b5be9bc65d3dedbdcc2fe48c105b75700de1087ba93f581a',
            'e13ddf43b9524f0cfdf23b8ac89b1bcdc21bb9030d5a80637a511f84c2c807e6',
            'ff87370119a48b8f78b8ff96476bfb1f0a317339922eb6d526859674f1349bd7']
        c = 0
        while (c < 14):
            h = self.hash("0" + str(c + 1).zfill(2) + ".jpg")
            if (h != middlehashes[c]):
                raise Error("recovered image does not match")
            c += 1

    @check("compiles")
    def last_image(self):
        """recovers 015.jpg correctly"""
        self.include("card.raw")
        self.spawn("./recover card.raw").exit(0)
        hash015 = '49442513773931634fc572de401bb44d6d91069b23113e86a16336f07d69021d'
        if self.hash("015.jpg") != hash015:
            raise Error("recovered image does not match")
