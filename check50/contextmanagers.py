import contextlib


@contextlib.contextmanager
def nullcontext(entry_result=None):
    """This is just contextlib.nullcontext but that function is only available in 3.7+."""
    yield entry_result
