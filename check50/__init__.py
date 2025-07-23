def _set_version():
    """Set check50 __version__"""
    global __version__
    from importlib.metadata import PackageNotFoundError, version
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

# Discourage use of check50 in the interactive mode, due to a naming conflict of
# the `_` variable. check50 uses it for translations, but Python stores the
# result of the last expression in a variable called `_`.
import sys
if hasattr(sys, 'ps1') or sys.flags.interactive:
    import warnings
    warnings.warn(_("check50 is not intended for use in interactive mode. "
                    "Some behavior may not function as expected."))

from ._api import (
    import_checks,
    data, _data,
    exists,
    hash,
    include,
    run,
    log, _log,
    hidden,
    Failure, Mismatch, Missing, Config,
    configure
)


from . import regex
from .runner import check
from pexpect import EOF

__all__ = ["import_checks", "data", "exists", "hash", "include", "regex",
           "run", "log", "Failure", "Mismatch", "Missing", "check", "EOF",
           "Config", "configure"]
