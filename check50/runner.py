import collections
from contextlib import contextmanager
import concurrent.futures as futures
import enum
import functools
import inspect
import importlib
import gettext
import os
from pathlib import Path
import shutil
import signal
import tempfile
import traceback

import attr

from . import internal
from ._api import log, Failure, _copy, _log, _data

_check_names = []


@attr.s(slots=True)
class CheckResult:
    """Record returned by each check"""
    name = attr.ib()
    description = attr.ib()
    passed = attr.ib(default=None)
    log = attr.ib(default=attr.Factory(list))
    cause = attr.ib(default=None)
    data = attr.ib(default=attr.Factory(dict))
    dependency = attr.ib(default=None)

    @classmethod
    def from_check(cls, check, *args, **kwargs):
        """Create a check_result given a check function, automatically recording the name,
        the dependency, and the (translated) description.
        """
        return cls(name=check.__name__, description=_(check.__doc__ if check.__doc__ else check.__name__.replace("_", " ")),
                   dependency=check._check_dependency.__name__ if check._check_dependency else None,
                   *args,
                   **kwargs)

    @classmethod
    def from_dict(cls, d):
        """Create a CheckResult given a dict. Dict must contain at least the fields in the CheckResult.
        Throws a KeyError if not."""
        return cls(**{field.name: d[field.name] for field in attr.fields(cls)})



class Timeout(Failure):
    def __init__(self, seconds):
        super().__init__(rationale=_("check timed out after {} seconds").format(seconds))


@contextmanager
def _timeout(seconds):
    """Context manager that runs code block until timeout is reached.

    Example usage::

        try:
            with _timeout(10):
                do_stuff()
        except Timeout:
            print("do_stuff timed out")
    """

    def _handle_timeout(*args):
        raise Timeout(seconds)

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)


def check(dependency=None, timeout=60):
    """Mark function as a check.

    :param dependency: the check that this check depends on
    :type dependency: function
    :param timeout: maximum number of seconds the check can run
    :type timeout: int

    When a check depends on another, the former will only run if the latter passes.
    Additionally, the dependent check will inherit the filesystem of its dependency.
    This is particularly useful when writing e.g., a ``compiles`` check that compiles a
    student's program (and checks that it compiled successfully). Any checks that run the
    student's program will logically depend on this check, and since they inherit the
    resulting filesystem of the check, they will immidiately have access to the compiled
    program without needing to recompile.

    Example usage::

        @check50.check() # Mark 'exists' as a check
        def exists():
            \"""hello.c exists\"""
            check50.exists("hello.c")

        @check50.check(exists) # Mark 'compiles' as a check that depends on 'exists'
        def compiles():
            \"""hello.c compiles\"""
            check50.c.compile("hello.c")

        @check50.check(compiles)
        def prints_hello():
            \"""prints "Hello, world!\\\\n\"""
            # Since 'prints_hello', depends on 'compiles' it inherits the compiled binary
            check50.run("./hello").stdout("[Hh]ello, world!?\\n", "hello, world\\n").exit()

    """
    def decorator(check):

        # Modules are evaluated from the top of the file down, so _check_names will
        # contain the names of the checks in the order in which they are declared
        _check_names.append(check.__name__)
        check._check_dependency = dependency

        @functools.wraps(check)
        def wrapper(checks_root, dependency_state):
            # Result template
            result = CheckResult.from_check(check)
            # Any shared (returned) state
            state = None

            try:
                # Setup check environment, copying disk state from dependency
                internal.run_dir = checks_root / check.__name__
                src_dir = checks_root / (dependency.__name__ if dependency else "-")
                shutil.copytree(src_dir, internal.run_dir)
                os.chdir(internal.run_dir)

                # Run registered functions before/after running check and set timeout
                with internal.register, _timeout(seconds=timeout):
                    args = (dependency_state,) if inspect.getfullargspec(check).args else ()
                    state = check(*args)
            except Failure as e:
                result.passed = False
                result.cause = e.payload
            except BaseException as e:
                result.passed = None
                result.cause = {"rationale": _("check50 ran into an error while running checks!"),
                                "error": {
                                    "type": type(e).__name__,
                                    "value": str(e),
                                    "traceback": traceback.format_tb(e.__traceback__),
                                    "data" : e.payload if hasattr(e, "payload") else {}
                                }}
            else:
                result.passed = True
            finally:
                result.log = _log
                result.data = _data
                return result, state
        return wrapper
    return decorator


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

        # Grab all checks from the module
        checks = inspect.getmembers(check_module, lambda f: hasattr(f, "_check_dependency"))

        # Map each check to tuples containing the names of the checks that depend on it
        self.dependency_graph = collections.defaultdict(set)
        for name, check in checks:
            dependency = None if check._check_dependency is None else check._check_dependency.__name__
            self.dependency_graph[dependency].add(name)

        # Map each check name to its description
        self.check_descriptions = {name: check.__doc__ for name, check in checks}


    def run(self, files, working_area, targets=None):
        """
        Run checks concurrently.
        Returns a list of CheckResults ordered by declaration order of the checks in the imported module
        targets allows you to limit which checks run. If targets is false-y, all checks are run.
        """
        graph = self.build_subgraph(targets) if targets else self.dependency_graph

        # Ensure that dictionary is ordered by check declaration order (via self.check_names)
        # NOTE: Requires CPython 3.6. If we need to support older versions of Python, replace with OrderedDict.
        results = {name: None for name in self.check_names}
        checks_root = working_area.parent

        try:
            max_workers = int(os.environ.get("CHECK50_WORKERS"))
        except (ValueError, TypeError):
            max_workers = None

        with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Start all checks that have no dependencies
            not_done = set(executor.submit(run_check(name, self.checks_spec, checks_root))
                           for name in graph[None])
            not_passed = []

            while not_done:
                done, not_done = futures.wait(not_done, return_when=futures.FIRST_COMPLETED)
                for future in done:
                    # Get result from completed check
                    result, state = future.result()
                    results[result.name] = result
                    if result.passed:
                        # Dispatch dependent checks
                        for child_name in graph[result.name]:
                            not_done.add(executor.submit(
                                run_check(child_name, self.checks_spec, checks_root, state)))
                    else:
                        not_passed.append(result.name)

        for name in not_passed:
            self._skip_children(name, results)

        # Don't include checks we don't have results for (i.e. in the case that targets != None) in the list.
        return list(filter(None, results.values()))


    def build_subgraph(self, targets):
        """
        Build minimal subgraph of self.dependency_graph that contains each check in targets
        """
        checks = self.dependencies_of(targets)
        subgraph = collections.defaultdict(set)
        for dep, children in self.dependency_graph.items():
            # If dep is not a dependency of any target,
            # none of its children will be either, may as well skip.
            if dep is not None and dep not in checks:
                continue
            for child in children:
                if child in checks:
                    subgraph[dep].add(child)
        return subgraph


    def dependencies_of(self, targets):
        """Get all unique dependencies of the targetted checks (tartgets)."""
        inverse_graph = self._create_inverse_dependency_graph()
        deps = set()
        for target in targets:
            if target not in inverse_graph:
                raise internal.Error(_("Unknown check: {}").format(e.args[0]))
            curr_check = target
            while curr_check is not None and curr_check not in deps:
                deps.add(curr_check)
                curr_check = inverse_graph[curr_check]
        return deps


    def _create_inverse_dependency_graph(self):
        """Build an inverse dependency map, from a check to its dependency."""
        inverse_dependency_graph = {}
        for check_name, dependents in self.dependency_graph.items():
            for dependent_name in dependents:
                inverse_dependency_graph[dependent_name] = check_name
        return inverse_dependency_graph


    def _skip_children(self, check_name, results):
        """
        Recursively skip the children of check_name (presumably because check_name
        did not pass).
        """
        for name in self.dependency_graph[check_name]:
            if results[name] is None:
                results[name] = CheckResult(name=name, description=self.check_descriptions[name],
                                            passed=None,
                                            dependency=check_name,
                                            cause={"rationale": _("can't check until a frown turns upside down")})
                self._skip_children(name, results)


class run_check:
    """
    Hack to get around the fact that `pickle` can't serialize closures.
    This class is essentially a function that reimports the check module and runs the check.
    """

    def __init__(self, check_name, spec, checks_root, state=None):
        self.check_name = check_name
        self.spec = spec
        self.checks_root = checks_root
        self.state = state

    def __call__(self):
        mod = importlib.util.module_from_spec(self.spec)
        self.spec.loader.exec_module(mod)
        internal.check_running = True
        try:
            return getattr(mod, self.check_name)(self.checks_root, self.state)
        finally:
            internal.check_running = False
