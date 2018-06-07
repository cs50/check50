def _set_version():
    """ Set check50 version, hiding variables from autocompleter.  """
    global __version__
    from pkg_resources import get_distribution, DistributionNotFound
    import os
    # https://stackoverflow.com/questions/17583443/what-is-the-correct-way-to-share-package-version-with-setup-py-and-the-package
    try:
        _dist = get_distribution("check50")
        # Normalize path for cross-OS compatibility.
        _dist_loc = os.path.normcase(_dist.location)
        _here = os.path.normcase(__file__)
        if not _here.startswith(os.path.join(_dist_loc, "check50")):
            # This version is not installed, but another version is.
            raise DistributionNotFound
    except DistributionNotFound:
        __version__ = "locally installed, no version information available"
    else:
        __version__ = _dist.version

_set_version()

from .internal.builtins import run, require, match
from .internal.errors import Error, Mismatch
from .internal.logger import log
from .internal.globals import check_dir
from .runner import check
