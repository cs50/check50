# ENABLE_CHECK50_ASSERT = 1
import check50

# Imported by assertions_rewrite_imported via check50.import_checks().
# Passes only if the asserts in *this* file were rewritten, even though the
# importing checks file does not enable rewriting itself.
# https://github.com/cs50/check50/issues/393

@check50.check()
def imported_rewritten():
    stdout = "Hello, world!"
    try:
        assert stdout == "Namespaces are one honking great idea."
    except check50.Mismatch:
        pass

    try:
        assert stdout in "Now is better than never."
    except check50.Missing:
        pass
