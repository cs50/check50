import unittest

from . import *

suite = unittest.TestLoader().discover("tests", pattern="*_tests.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
