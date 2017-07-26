import os
import sys

sys.path.append(os.getcwd())

from check50 import *

class Project(Checks): 

    @check()
    def exists(self):
        """project exists."""
        pass
