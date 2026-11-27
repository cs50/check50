import check50

assertions_rewrite_imported_base = check50.import_checks("../assertions_rewrite_imported_base")
from assertions_rewrite_imported_base import *

# This file does not enable rewriting, so its own asserts stay plain AssertionErrors.

@check50.check()
def importer_not_rewritten():
    stdout = "Hello, world!"
    try:
        assert stdout == "Although never is often better than *right* now."
    except AssertionError:
        pass
