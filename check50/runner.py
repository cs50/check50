import collections
import enum
import functools
import os
import multiprocessing as mp
import traceback
import tempfile
import inspect

import attr
import shutil

from . import internal
from .api import log, _log, Failure, _copy

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

    @classmethod
    def from_check(cls, check, *args, **kwargs):
        return cls(name=check.__name__, description=check.__doc__, *args, **kwargs)


def check(dependency=None):
    """ Decorator for checks. """
    def decorator(check):

        check_names.append(check.__name__)
        check._check_dependency = dependency

        @functools.wraps(check)
        def wrapper(checks_root, results):
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
                results.put(result)
        return wrapper
    return decorator


# Probably shouldn't be a class
class CheckRunner:
    def __init__(self, check_module):
        self.checks = [check for _, check in inspect.getmembers(check_module, lambda f: hasattr(f, "_check_dependency"))]

        # map each check to the check(s) that depend on it
        self.child_map = collections.defaultdict(set)
        for check in self.checks:
            if check._check_dependency is not None:
                self.child_map[check._check_dependency.__name__].add(check)

    def run(self, files):
        results = {name: None for name in check_names}
        queue = mp.Queue()
        with tempfile.TemporaryDirectory() as checks_root:
            dst_dir = os.path.join(checks_root, "-")
            os.mkdir(dst_dir)

            for filename in files:
                _copy(filename, dst_dir)

            def start(check):
                proc = mp.Process(target=check, args=(checks_root, queue))
                proc.start()
                return proc


            procs = {check.__name__ : start(check)
                        for check in self.checks
                        if check._check_dependency is None}
            while procs:
                # TODO: This will currently block if we don't get a result for a check due to some error. Fix this.
                result = queue.get()
                results[result.name] = result

                # This should return immidiately since the last thing a check does per the decorator is push to the queue
                procs[result.name].join()
                del procs[result.name]

                if result.status is Status.Pass:
                    procs.update({
                        check.__name__ : start(check)
                            for check in self.child_map.get(result.name, [])
                    })
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

