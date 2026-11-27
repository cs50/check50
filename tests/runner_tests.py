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

# Just test spawn under OS X due to a bug with "fork": https://bugs.python.org/issue33725
if sys.platform == "darwin":
    SUPPORTED_START_METHODS = ("spawn",)
else:
    SUPPORTED_START_METHODS = tuple(multiprocessing.get_all_start_methods())


class TestMultiprocessingStartMethods(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

        self._run_root_dir = check50.internal.run_root_dir
        self._check_dir = check50.internal.check_dir

    def tearDown(self):
        self.working_directory.cleanup()
        check50.internal.run_root_dir = self._run_root_dir
        check50.internal.check_dir = self._check_dir

    def test_unpicklable_attribute(self):
        checks_path = CHECKS_DIRECTORY / "unpicklable_attribute/__init__.py"
        check_name = "foo"
        spec = importlib.util.spec_from_file_location("checks", checks_path)

        # Execute the module once in the main process, as the Runner does too,
        # so sys.excepthook holds the unpicklable lambda when run_check captures it
        check_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check_module)

        for start_method in SUPPORTED_START_METHODS:
            with self.subTest(start_method=start_method):
                ctx = multiprocessing.get_context(start_method)

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

        for start_method in SUPPORTED_START_METHODS:
            with self.subTest(start_method=start_method):
                ctx = multiprocessing.get_context(start_method)

                # The layout a Runner prepares: run_root_dir/-/ holds the student's files, and the
                # check copies it to run_root_dir/<check name>/ before running
                with tempfile.TemporaryDirectory() as run_root:
                    run_root = pathlib.Path(run_root)
                    (run_root / "-").mkdir()
                    (run_root / "-" / "foo.py").touch()
                    check50.internal.run_root_dir = run_root
                    check50.internal.check_dir = checks_path.parent

                    with ctx.Pool(1) as pool:
                        result, _ = pool.apply(check50.runner.run_check(check_name, spec))

                self.assertEqual(result.name, check_name)
                self.assertTrue(result.passed, msg=f"check did not pass under {start_method}: {result.cause}")

    def test_assertion_rewrite_override_reaches_child(self):
        """The --assertion-rewrite override must apply to import_checks() inside the child.

        Workers re-import the checks module, which re-runs import_checks(). With the override set
        in the parent only, a start method that does not inherit memory would see None in the child
        and fall back to the imported file's comment flag (https://github.com/cs50/check50/issues/393).
        """
        # The imported checks file has no comment flag, so it gets rewritten only if the override
        # made it into the child. Its check passes only if the assert was rewritten.
        check_dir = pathlib.Path(self.working_directory.name)
        (check_dir / "base").mkdir()
        (check_dir / "base" / ".cs50.yaml").write_text("check50:\n  checks: __init__.py\n")
        (check_dir / "base" / "__init__.py").write_text(
            "import check50\n"
            "@check50.check()\n"
            "def imported():\n"
            "    try:\n"
            "        assert 'foo' == 'bar'\n"
            "    except check50.Mismatch:\n"
            "        pass\n"
        )
        checks_path = check_dir / "__init__.py"
        checks_path.write_text(
            "import check50\n"
            "base = check50.import_checks('./base')\n"
            "from base import *\n"
        )
        spec = importlib.util.spec_from_file_location("checks", checks_path)

        self.addCleanup(setattr, check50.internal, "assertion_rewrite", check50.internal.assertion_rewrite)

        for start_method in SUPPORTED_START_METHODS:
            with self.subTest(start_method=start_method):
                ctx = multiprocessing.get_context(start_method)

                with tempfile.TemporaryDirectory() as run_root:
                    run_root = pathlib.Path(run_root)
                    (run_root / "-").mkdir()
                    check50.internal.run_root_dir = run_root
                    check50.internal.check_dir = check_dir
                    check50.internal.assertion_rewrite = True

                    with ctx.Pool(1) as pool:
                        result, _ = pool.apply(check50.runner.run_check("imported", spec))

                self.assertTrue(result.passed, msg=f"imported check not rewritten under {start_method}: {result.cause}")


if __name__ == "__main__":
    unittest.main()
