import collections
import enum
import hashlib
import imp
import os
import re
import signal
import sys
import time
import traceback
import unittest
import urllib.parse as url

import shutil
import shlex

from .internal import globals, logger, register

import multiprocessing as mp

class Status(enum.Enum):
    Pass = True
    Fail = False
    Skip = None
    Error = None

def check(dependency=None):
    """ Decorator for checks. """
    def decorator(f):

        globals.test_cases.append(f.__name__)
        f._check_dependency = dependency

        @wraps(f)
        def wrapper(results):
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
                dst_dir = globals.check_dir = os.path.join(globals.checks_root, f.__name__)
                src_dir = os.path.join(globals.checks_root, dependency or "_")
                shutil.copytree(src_dir, dst_dir)
                os.chdir(self.dir)

                f()
            except Error as e:
                result["status"] = e.result
                result["helpers"] = e.helpers
                result["rationale"] = e.rationale
            except BaseException as e:
                result["status"] = Status.Error
                result["rationale"] = "check50 ran into an error while running checks!"
                logger.log(repr(e))
                for line in traceback.format_tb(e.__traceback__):
                    logger.log(line.rstrip())
                logger.log("Contact sysadmins@cs50.harvard.edu with the URL of this check!")
            else:
                result["status"] = Status.Pass
            finally:
                result["log"] = logger._log.clone()
                results.put(result)

        return wrapper
    return decorator

class CheckRunner:
    def __init__(self, check_module):
        self.checks = inspect.getmembers(check_module, lambda f: hasattr(f, "_check_dependency"))

        # map each check to the check(s) that depend on it
        self.child_map = collections.defaultdict(set)
        for check in inspect.getmembers(check_module, hasattr(f, "_check_dependency")):
            self.child_map[check._check_dependency.__name__].add(check)

    def run(self):
        results = {}
        queue = mp.Queue()

        check50.internal.check_dir

        def start(check):
            proc = mp.Process(target=check, args=(queue,))
            proc.start()
            return proc

        procs = {check.__name__ : start(check) for check in self.checks if check._check_dependency is None}
        while procs:
            result = queue.get()
            self.results[result.name] = result
            procs.update({check.__name__ : start(check) for check in self.child_map[result.name]})

            # This should return immidiately since the last thing a check does per the decorator is push to the queue
            procs[result.name].join()
            del procs[result.name]

        return results

# class CheckRunner:
    # def __init__(self, check_module, executor=futures.ThreadPoolExecutor):
        # self.check_module = check_module
        # self.executor = executor
        # self.results = {}

        # # map each check to the check(s) that depend on it
        # self.child_map = collections.defaultdict(set)
        # checks =
        # for check in inspect.getmembers(check_module, hasattr(f, "_check_dependency")):
            # child_map[check._check_dependency].add(check)


    # def run(self, executor=futures.ProcessPoolExecutor):
        # first_checks = (check.__name__ for check in self.checks._check_list if check._check_parent is None)
        # futures = {self.dispatch(check.__name__) : check for check in first_checks}
        # not_done = set(futures.keys())

        # while not_done:
            # done, not_done = futures.wait(not_done, return_when=futures.FIRST_COMPLETED)
            # for future in done:
                # check = futures[future]
                # log = future.result()
                # exception = future.exception()
                # if exception is None:
                    # self.record_success(check, log)
                    # for child in self.children[check]:
                        # futures[self.dispatch(child)] = child
                # else:
                    # self.record_failure(check, exception)
                    # self.skip_children(check)



    # def skip_children(self, check):
        # for child in self.children[check]
            # if self.results.get(child) is not None:
                # self.record_skip(check, Status.SKIP)
                # self.skip_children(child)


    # def dispatch(self, check_name):
        # def run_check():
            # check = self.checks()
            # getattr(self.checks, check_name)(check)
            # return check._log
        # return self.executor.submit(run_check)

    # def record_ok(self, check, log, status):
        # self.results[check] = {
            # "description": getattr(self.checks, check).__doc__,
            # "helpers": None,
            # "log": log,
            # "helpers": None,
            # "rationale": None,
            # "status": status
        # }

    # def record_err(self, check, log, exc):
        # if isinstance(exc, Error):
            # status = Status.FAIL
            # rationale = exc.rationale
            # helpers = exc.helpers
        # else:
            # status = Status.ERROR
            # rationale = "check50 ran into an error while running checks!"
            # helpers = None

            # log.append(str(exc))
            # log += (line.rstrip() for line in traceback.format_tb(exc.__traceback__))
            # log.append("Contact sysadmins@cs50.harvard.edu with the URL of this check!")

        # self.results[check] = {
            # "description": getattr(self.checks, check).__doc__,
            # "helpers": helpers,
            # "log" log,
            # "rationale": rationale,
            # "status": status
        # }


if __name__ == "__main__":
    main()
