import collections
import concurrent.futures as futures
import enum
import functools
import os
import multiprocessing as mp
import traceback
import tempfile
import inspect
import importlib

import attr
import shutil

from . import internal
from .api import log, Failure, _copy, _log

check_names = []

class Status(enum.Enum):
    Pass = True
    Fail = False
    Skip = None


@attr.s
class CheckResult:
    name = attr.ib(default=None)
    description = attr.ib(default=None)
    status = attr.ib(default=None)
    log = attr.ib(default=[])
    rationale = attr.ib(default=None)
    help = attr.ib(default=None)
    data = attr.ib(default=None)
    _pid = attr.ib(default=attr.Factory(lambda: os.getpid()), init=False)

    @classmethod
    def from_check(cls, check, *args, **kwargs):
        return cls(name=check.__name__, description=check.__doc__, *args, **kwargs)


def check(dependency=None):
    """ Decorator for checks. """
    def decorator(check):

        # Modules are evaluated from the top of the file down, so check_names will
        # contain the names of the checks in the order in which they are declared
        check_names.append(check.__name__)
        check._check_dependency = dependency

        @functools.wraps(check)
        def wrapper(checks_root):
            # Result template
            result = CheckResult.from_check(check)
            try:
                # Setup check environment
                dst_dir = internal.run_dir = os.path.join(checks_root, check.__name__)
                src_dir = os.path.join(checks_root, dependency.__name__ if dependency is not None else "-")
                shutil.copytree(src_dir, dst_dir)
                os.chdir(internal.run_dir)

                with internal.register:
                    check()

            except Failure as e:
                result.status = Status.Fail
                result.help = e.help
                result.rationale = e.rationale
            except BaseException as e:
                result.status = Status.Skip
                result.rationale = "check50 ran into an error while running checks!"
                log(repr(e))
                for line in traceback.format_tb(e.__traceback__):
                    log(line.rstrip())
                log("Contact sysadmins@cs50.harvard.edu with the URL of this check!")
            else:
                result.status = Status.Pass
            finally:
                result.log = _log
                return result
        return wrapper
    return decorator

class run_check:
    """
    Hack to get around the fact that `pickle` can't serialize functions that capture their surrounding context
    This class is essentially a function that reimports the check module and runs the check
    """
    def __init__(self, check_name, spec, checks_root):
        self.check_name = check_name
        self.spec = spec
        self.checks_root = checks_root

    def __call__(self):
        mod = importlib.util.module_from_spec(self.spec)
        self.spec.loader.exec_module(mod)
        return getattr(mod, self.check_name)(self.checks_root)


# Probably shouldn't be a class
class CheckRunner:
    def __init__(self, check_module):
        self.checks_spec = check_module.__spec__
        self.checks = [check for _, check in inspect.getmembers(check_module, lambda f: hasattr(f, "_check_dependency"))]

        # map each check to the check(s) that depend on it
        self.child_map = collections.defaultdict(set)
        for check in self.checks:
            if check._check_dependency is not None:
                self.child_map[check._check_dependency.__name__].add(check)

    def run(self, files):
        # Ensure that dictionary is ordered by check_declaration order (via check_names)
        results = { name : None for name in check_names }
        executor = futures.ProcessPoolExecutor()

        with tempfile.TemporaryDirectory() as checks_root:
            dst_dir = os.path.join(checks_root, "-")
            os.mkdir(dst_dir)

            for filename in files:
                _copy(filename, dst_dir)

            not_done = set(executor.submit(run_check(check.__name__, self.checks_spec, checks_root))
                for check in self.checks if check._check_dependency is None)

            while not_done:
                done, not_done = futures.wait(not_done, return_when=futures.FIRST_COMPLETED)
                for future in done:
                    result = future.result()
                    results[result.name] = result
                    if result.status is Status.Pass:
                        for child in self.child_map[result.name]:
                            not_done.add(executor.submit(run_check(child.__name__, self.checks_spec, checks_root)))
                    else:
                        self._skip_children(result.name, results)
        return results

    def _skip_children(self, check_name, results):
        for child in self.child_map[check_name]:
            name = child.__name__
            if results[name] is None:
                results[name] = CheckResult.from_check(child,
                                            status=Status.Skip,
                                            rationale="can't check until a frown turns upside down")
                self._skip_children(name, results)

