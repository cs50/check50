import collections
import concurrent.futures as futures
import enum
import functools
import inspect
import importlib
import os
from pathlib import Path
import shutil
import tempfile
import traceback

import attr

from . import internal
from .api import log, Failure, _copy, _log

_check_names = []


class Status(enum.Enum):
    Pass = True
    Fail = False
    Skip = None


@attr.s(slots=True)
class CheckResult:
    name = attr.ib(default=None)
    description = attr.ib(default=None)
    status = attr.ib(default=None, converter=Status)
    log = attr.ib(default=[])
    # Better name? This contains information about why check didn't pass (i.e. failed or skipped)
    why = attr.ib(default=None)
    data = attr.ib(default={})
    _pid = attr.ib(default=attr.Factory(os.getpid))

    @classmethod
    def from_check(cls, check, *args, **kwargs):
        return cls(name=check.__name__, description=check.__doc__, *args, **kwargs)


def check(dependency=None):
    """ Decorator for checks. """
    def decorator(check):

        # Modules are evaluated from the top of the file down, so _check_names will
        # contain the names of the checks in the order in which they are declared
        _check_names.append(check.__name__)
        check._check_dependency = dependency

        @functools.wraps(check)
        def wrapper(checks_root):
            # Result template
            result = CheckResult.from_check(check)
            try:
                # Setup check environment
                internal.run_dir = checks_root / check.__name__
                src_dir = checks_root / (dependency.__name__ if dependency else "-")
                shutil.copytree(src_dir, internal.run_dir)
                os.chdir(internal.run_dir)

                # Run registered functions before/after running check
                with internal.register:
                    check()
            except Failure as e:
                result.status = Status.Fail
                result.why = e.asdict()
            except BaseException as e:
                result.status = Status.Skip
                result.why = {"rationale": "check50 ran into an error while running checks!"}
                log(repr(e))
                for line in traceback.format_tb(e.__traceback__):
                    log(line.rstrip())
                log("Contact sysadmins@cs50.harvard.edu with the URL of this check!")
            else:
                result.status = Status.Pass
            finally:
                result.log = _log
                result.data = internal._data
                return result
        return wrapper
    return decorator


# Probably shouldn't be a class
class CheckRunner:
    def __init__(self, checks_path):
        # TODO: Naming the module "checks" is arbitray. Better name?
        self.checks_spec = importlib.util.spec_from_file_location("checks", checks_path)

        # Clear check_names, import module, then save check_names. Not thread safe.
        # Ideally, there'd be a better way to extract declaration order than @check mutating global state,
        # but there are a lot of subtleties with using `inspect` or similar here
        _check_names.clear()
        check_module = importlib.util.module_from_spec(self.checks_spec)
        self.checks_spec.loader.exec_module(check_module)
        self.check_names = _check_names.copy()
        _check_names.clear()

        # Map each check to tuples containing the names and descriptions of the checks that depend on it
        self.child_map = collections.defaultdict(set)
        for name, check in inspect.getmembers(check_module, lambda f: hasattr(f, "_check_dependency")):
            dependency = check._check_dependency.__name__ if check._check_dependency is not None else None
            self.child_map[dependency].add((name, check.__doc__))

        # TODO: Check for deadlocks (Khan's algorithm?)

    def run(self, files):
        """Run checks concurrently.
        Returns a list of CheckResults ordered by declaration order of the checks in the imported module"""

        # Ensure that dictionary is ordered by check declaration order (via self.check_names)
        # NOTE: Requires CPython 3.6. If we need to support older versions of Python, replace with OrderedDict.
        results = {name: None for name in self.check_names}
        executor = futures.ProcessPoolExecutor()

        with tempfile.TemporaryDirectory() as checks_root:
            checks_root = Path(checks_root)

            # Setup initial check environment
            dst_dir = checks_root / "-"
            os.mkdir(dst_dir)
            for filename in map(Path, files):
                _copy(filename, dst_dir)

            # Start all checks that have no dependencies
            not_done = set(executor.submit(run_check(name, self.checks_spec, checks_root))
                           for name, _ in self.child_map[None])
            not_passed = []

            while not_done:
                done, not_done = futures.wait(not_done, return_when=futures.FIRST_COMPLETED)
                for future in done:
                    result = future.result()
                    results[result.name] = result
                    if result.status is Status.Pass:
                        for name, _ in self.child_map[result.name]:
                            not_done.add(executor.submit(
                                run_check(name, self.checks_spec, checks_root)))
                    else:
                        not_passed.append(result.name)

        for name in not_passed:
            self._skip_children(name, results)

        return results.values()

    def _skip_children(self, check_name, results):
        """Recursively skip the children of check_name (presumably because check_name did not pass)."""
        for name, description in self.child_map[check_name]:
            if results[name] is None:
                results[name] = CheckResult(name=name,
                                            description=description,
                                            status=Status.Skip,
                                            why={"rationale": "can't check until a frown turns upside down"})
                self._skip_children(name, results)


class run_check:
    """Hack to get around the fact that `pickle` can't serialize closures.
    This class is essentially a function that reimports the check module and runs the check."""

    def __init__(self, check_name, spec, checks_root):
        self.check_name = check_name
        self.spec = spec
        self.checks_root = checks_root

    def __call__(self):
        mod = importlib.util.module_from_spec(self.spec)
        self.spec.loader.exec_module(mod)
        return getattr(mod, self.check_name)(self.checks_root)
