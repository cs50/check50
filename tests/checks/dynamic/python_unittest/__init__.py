import check50
import unittest


@check50.check(dynamic=True)
def exists():
    """all files exist"""
    check50.include("some_tests.py")

    suite = unittest.TestLoader().discover('.', pattern="*tests.py")

    for test in iterate_tests(suite):
        create_check(test)


def create_check(unittest_test):
    """
    Helper function to create a check from a unittest TestCase
    """
    def prototype():
        result = unittest_test.run()
        if not result.wasSuccessful():
            failure = result.failures[0]
            reason = failure[1].strip()
            raise check50.Failure(reason)

    prototype.__name__ = unittest_test.id()
    prototype.__doc__ = f"{unittest_test.id()} passes"

    check50.check()(prototype)


def iterate_tests(test_suite_or_case):
    """
    Helper function to iterate through all test cases in a unittest suite or testcase.
    Iterate through all of the unittest test cases in 'test_suite_or_case'.
    src: https://github.com/testing-cabal/testtools/blob/bb6bc7aede0fc032f1db85b9cc033826d321142c/testtools/testsuite.py#L27
    """
    try:
        suite = iter(test_suite_or_case)
    except TypeError:
        yield test_suite_or_case
    else:
        for test in suite:
            yield from iterate_tests(test)
