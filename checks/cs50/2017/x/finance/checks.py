import os
import re
import sys

sys.path.append(os.getcwd())
from check50 import TestCase, Error, check

class Finance(TestCase):
    
    @check()
    def exists(self):
        """application.c exists."""
        super(Finance, self).exists("application.py")
