def _set_version():
    """Set check50 __version__"""
    global __version__
    from pkg_resources import get_distribution, DistributionNotFound
    import os
    # https://stackoverflow.com/questions/17583443/what-is-the-correct-way-to-share-package-version-with-setup-py-and-the-package
    try:
        dist = get_distribution("check50")
        # Normalize path for cross-OS compatibility.
        dist_loc = os.path.normcase(dist.location)
        here = os.path.normcase(__file__)
        if not here.startswith(os.path.join(dist_loc, "check50")):
            # This version is not installed, but another version is.
            raise DistributionNotFound
    except DistributionNotFound:
        __version__ = "locally installed, no version information available"
    else:
        __version__ = dist.version


def _setup_translation():
    import gettext
    from pkg_resources import resource_filename
    global _translation
    _translation = gettext.translation(
        "check50", resource_filename("check50", "locale"), fallback=True)
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
