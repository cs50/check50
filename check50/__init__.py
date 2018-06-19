def _set_version():
    """ Set check50 __version__ """
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


# Encapsulated inside a function so its local variables/imports aren't seen by autocompleters
_set_version()
del _set_version

from .api import run, exists, include, hash, log, _log, diff, Failure, Mismatch, import_module, append_code
from .runner import check
