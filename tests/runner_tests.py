import check50
import check50.runner

import importlib
import multiprocessing
import os
import pathlib
import sys
import tempfile
import unittest


CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"

# Every start method the platform offers. check50 leaves the method at Python's default, and that
# default has changed under it: Linux moved from fork to forkserver in 3.14. Both forkserver and spawn
# start the child from a fresh interpreter, so state set in the parent's modules must be carried over
# explicitly (run_check.CROSS_PROCESS_ATTRIBUTES), or every check fails in the child.
# Just test spawn under OS X due to a bug with "fork": https://bugs.python.org/issue33725
if sys.platform == "darwin":
    SUPPORTED_START_METHODS = ("spawn",)
else:
    SUPPORTED_START_METHODS = tuple(multiprocessing.get_all_start_methods())


class TestMultiprocessingStartMethods(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

        # Keep track of get_start_method
        # This function gets monkey patched to ensure run_check is aware of the multiprocessing context, 
        # without needing to explicitly pass the context to run_check.
        # The same behavior can't be achieved by multiprocessing.set_start_method as that can only run once per program
        # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
        self._get_start_method = multiprocessing.get_start_method

    def tearDown(self):
        self.working_directory.cleanup()
        multiprocessing.get_start_method = self._get_start_method

    def test_unpicklable_attribute(self):
        # Create the checks_spec and check_name needed for run_check
        checks_path = CHECKS_DIRECTORY / "unpicklable_attribute/__init__.py"
        check_name = "foo"
        spec = importlib.util.spec_from_file_location("checks", checks_path)

        # Execute the module once in the main process, as the Runner does too
        # This will set sys.excepthook to an unpicklable lambda
        check_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check_module)

        # For each available method
        for start_method in SUPPORTED_START_METHODS:
            with self.subTest(start_method=start_method):
                # Create a multiprocessing context for that method
                ctx = multiprocessing.get_context(start_method)

                # Monkey patch get_start_method() used by run_check to check for its method.
                # Python 3.13+ calls get_start_method(allow_none=True) internally while spawning,
                # so the replacement must accept that keyword argument.
                multiprocessing.get_start_method = lambda allow_none=False, _method=start_method: _method

                # Start and join each check process
                p = ctx.Process(target=check50.runner.run_check(check_name, spec))
                p.start()
                p.join()
                self.assertEqual(p.exitcode, 0)

    def test_parent_state_reaches_child(self):
        """A check must see the parent's run_root_dir under every start method.

        run_check captures internal.run_root_dir in the parent and restores it in the child. If that
        is skipped for a start method that does not inherit the parent's memory, the child sees None,
        the check errors before it starts, and every check in the run comes back without a result;
        this is what happened when Python 3.14 made forkserver the default on Linux.
        """
        checks_path = CHECKS_DIRECTORY / "exists/check.py"
        check_name = "exists"
        spec = importlib.util.spec_from_file_location("checks", checks_path)
        check_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check_module)

        for start_method in SUPPORTED_START_METHODS:
            with self.subTest(start_method=start_method):
                ctx = multiprocessing.get_context(start_method)
                multiprocessing.get_start_method = lambda allow_none=False, _method=start_method: _method

                # The layout a Runner prepares: run_root_dir/-/ holds the student's files, and the
                # check copies it to run_root_dir/<check name>/ before running
                with tempfile.TemporaryDirectory() as run_root:
                    run_root = pathlib.Path(run_root)
                    (run_root / "-").mkdir()
                    (run_root / "-" / "foo.py").touch()
                    check50.internal.run_root_dir = run_root
                    check50.internal.check_dir = checks_path.parent

                    # Run the check in a child and get its CheckResult back
                    with ctx.Pool(1) as pool:
                        result, _ = pool.apply(check50.runner.run_check(check_name, spec))

                self.assertEqual(result.name, check_name)
                self.assertTrue(result.passed, msg=f"check did not pass under {start_method}: {result.cause}")


if __name__ == "__main__":
    unittest.main()