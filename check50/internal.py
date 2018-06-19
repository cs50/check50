"""
Additional check50 internals exposed to extension writers in addition to the standard API
"""

from contextlib import contextmanager

# Directory containing the check and its associated files
check_dir = None

# Temporary directory in which check is being run
run_dir = None


class Register:
    def __init__(self, after_onces=[], before_everies=[], after_everies=[], resets=[]):
        self._before_everies = list(before_everies)
        self._after_everies = list(after_everies)
        self._after_onces = list(after_onces)
        self._resets = list(resets)

    def after_once(self, func):
        """run func once at the end of the check, then discard func"""
        self._after_onces.append(func)

    def after_every(self, func):
        """run func at the end of every check"""
        self._after_everies.append(func)

    def before_every(self, func):
        """run func at the start of every check"""
        self._before_everies.append(func)

    def reset(self, func):
        """runs func to reset state between checks"""
        self._resets.append(func)

    def __enter__(self):
        for f in self._resets:
            f()

        for f in self._before_everies:
            f()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Only run 'afters' when check has passed
        if exc_type is None:
            for f in self._after_onces:
                f()

            for f in self._after_everies:
                f()

        self._after_onces = []


register = Register()

_data = {}
register.reset(lambda : _data.clear())

def data(**kwargs):
    _data.update(kwargs)
