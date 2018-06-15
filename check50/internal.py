"""
Additional check50 internals exposed to extension writers in addition to the standard API
"""

from contextlib import contextmanager

# Directory containing the check and its associated files
check_dir = None

# Temporary directory in which check is being run
run_dir = None


class Register:
    def __init__(self, befores=[], afters=[], resets=[]):
        self._befores = befores
        self._afters = afters
        self._resets = resets

    def before(self, func):
        self._befores.append(func)

    def after(self, func):
        self._afters.append(func)

    def reset(self, func):
        self._resets.append(func)

    def __enter__(self):
        for f in self._resets:
            f()

        for f in self._befores:
            f()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Only run 'afters' when check has passed
        if exc_type is None:
            for f in self._afters:
                f()


register = Register()

_data = {}


def data(**kwargs):
    _data.update(kwargs)
