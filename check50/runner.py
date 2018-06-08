import collections
import enum
import functools
import os
import multiprocessing as mp
import traceback
import tempfile
import inspect

import shutil

from .internal import globals, logger, register, utils
from .internal.errors import Error


class Status(enum.Enum):
    Pass = True
    Fail = False
    Skip = None


def check(dependency=None):
    """ Decorator for checks. """
    def decorator(f):

        globals.check_names.append(f.__name__)
        f._check_dependency = dependency

        @functools.wraps(f)
        def wrapper(checks_root, results):
            # Result template
            result = {
                "name": f.__name__,
                "description": f.__doc__,
                "helpers": None,
                "status": None,
                "log": None,
                "rationale": None,

            }
            try:
                # Setup check environment
                dst_dir = globals.cwd = os.path.join(checks_root, f.__name__)
                src_dir = os.path.join(checks_root, dependency.__name__ if dependency is not None else "_")
                shutil.copytree(src_dir, dst_dir)
                os.chdir(globals.cwd)

                register._exec_before()
                f()
                register._exec_after()
            except Error as e:
                result["status"] = e.result
                result["helpers"] = e.helpers
                result["rationale"] = e.rationale
            except BaseException as e:
                result["status"] = Status.Skip
                result["rationale"] = "check50 ran into an error while running checks!"
                logger.log(repr(e))
                for line in traceback.format_tb(e.__traceback__):
                    logger.log(line.rstrip())
                logger.log("Contact sysadmins@cs50.harvard.edu with the URL of this check!")
            else:
                result["status"] = Status.Pass
            finally:
                result["log"] = logger._log
                results.put(result)
        return wrapper
    return decorator

class CheckRunner:
    def __init__(self, check_module):
        self.checks = [check for _, check in inspect.getmembers(check_module, lambda f: hasattr(f, "_check_dependency"))]

        # map each check to the check(s) that depend on it
        self.child_map = collections.defaultdict(set)
        for check in self.checks:
            if check._check_dependency is not None:
                self.child_map[check._check_dependency.__name__].add(check)

    def run(self, files):
        results = {}
        queue = mp.Queue()
        with tempfile.TemporaryDirectory() as checks_root:
            dst_dir = os.path.join(checks_root, "_")
            os.mkdir(dst_dir)

            for filename in files:
                utils.copy(filename, dst_dir)

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
                name = result["name"]
                results[name] = result
                procs.update({
                    check.__name__ : start(check)
                        for check in self.child_map.get(name, [])
                })
                # This should return immidiately since the last thing a check does per the decorator is push to the queue
                procs[name].join()
                del procs[name]

        return results
