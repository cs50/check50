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
CHECK50_SUPPORTED_START_METHODS = ("fork", "spawn")


# Just test spawn under OS X due to a bug with "fork": https://bugs.python.org/issue33725
if sys.platform == "darwin":
    SUPPORTED_START_METHODS = ("spawn",)

# Don't test forkserver under linux, serves no usecase for check50
else:
    SUPPORTED_START_METHODS = tuple(set(CHECK50_SUPPORTED_START_METHODS) & set(multiprocessing.get_all_start_methods()))


class TestMultiprocessingStartMethods(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()

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
                # Create a multiprocessing context for that method.
                # run_check no longer consults multiprocessing.get_start_method(), so no
                # monkey patching is needed; the context alone decides how the child starts.
                ctx = multiprocessing.get_context(start_method)

                # Start and join each check process
                p = ctx.Process(target=check50.runner.run_check(check_name, spec))
                p.start()
                p.join()
                self.assertEqual(p.exitcode, 0)


if __name__ == "__main__":
    unittest.main()