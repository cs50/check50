def _set_version():
    """Set check50 __version__"""
    global __version__
    from importlib.metadata import PackageNotFoundError, version
    import os
    # https://stackoverflow.com/questions/17583443/what-is-the-correct-way-to-share-package-version-with-setup-py-and-the-package
    try:
        __version__ = version("check50")
    except PackageNotFoundError:
        __version__ = "UNKNOWN"


def _setup_translation():
    import gettext
    from importlib.resources import files
    global _translation
    _translation = gettext.translation(
        "check50", str(files("check50").joinpath("locale")), fallback=True)
    _translation.install()



# Encapsulated inside a function so their local variables/imports aren't seen by autocompleters
_set_version()
_setup_translation()

from ._api import (
    import_checks,
    data, _data,
    exists,
    hash,
    include,
    run,
    log, _log,
    hidden,
    Failure, Mismatch, Missing
)


from . import regex
from .runner import check
from pexpect import EOF

__all__ = ["import_checks", "data", "exists", "hash", "include", "regex",
           "run", "log", "Failure", "Mismatch", "Missing", "check", "EOF"]
