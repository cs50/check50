import os
import sys

sys.path.append(os.getcwd())

from check50 import *

class Mashup(Checks): 

    @check()
    def exists(self):
        """mashup exists."""
        pass
