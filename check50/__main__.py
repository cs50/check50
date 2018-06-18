import argparse
import importlib
import inspect
import itertools
import json
import logging
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import traceback
import time

import attr
import git
from pexpect.exceptions import EOF
import requests
from termcolor import cprint

from . import internal, __version__
from .api import Failure
from .runner import CheckRunner, Status, CheckResult


class InternalError(Exception):
    """Error during execution of check50."""

    def __init__(self, msg):
        self.msg = msg


def excepthook(cls, exc, tb):
    if cls is InternalError:
        cprint(exc.msg, "red", file=sys.stderr)
    elif cls is FileNotFoundError:
        cprint(f"{exc.filename} not found", "red", file=sys.stderr)
    elif cls is KeyboardInterrupt:
        cprint(f"check cancelled", "red")
    elif not issubclass(cls, Exception):
        # Class is some other BaseException, better just let it go
        return
    else:
        cprint("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!", "red", file=sys.stderr)

    if excepthook.verbose:
        traceback.print_exception(cls, exc, tb)

    sys.exit(1)


# Assume we should print tracebacks until we get command line arguments
excepthook.verbose = True
sys.excepthook = excepthook


class Encoder(json.JSONEncoder):
    """Custom class for JSON encoding."""

    def default(self, o):
        if o == EOF:
            return "EOF"
        elif isinstance(o, Status):
            return o.value

        return o.__dict__


def print_json(results):
    json.dump({"results": [attr.asdict(result) for result in results],
               "version": __version__},
               sys.stdout, cls=Encoder)


def print_ansi(results, log=False):
    for result in results:
        if result.status is Status.Pass:
            cprint(f":) {result.description}", "green")
        elif result.status is Status.Fail:
            cprint(f":( {result.description}", "red")
            if result.why.get("rationale") is not None:
                cprint(f"    {result.why['rationale']}", "red")
        elif result.status is Status.Skip:
            cprint(f":| {result.description}", "yellow")
            cprint(f"    {result.why.get('rationale') or 'check skipped'}", "yellow")

        if log:
            print(*(f"   {line}" for line in result.log), sep="\n")


def parse_identifier(identifier):
    # Find second "/" in identifier
    idx = identifier.find("/", identifier.find("/") + 1)
    if idx == -1:
        raise InternalError("invalid identifier")

    repo, remainder = identifier[:idx], identifier[idx+1:]

    try:
        branches = (line.split("\t")[1].replace("refs/heads/", "")
                        for line in git.Git().ls_remote(f"https://github.com/{repo}", heads=True).split("\n"))
    except git.GitError:
        raise InternalError("invalid identifier")

    for branch in branches:
        if remainder.startswith(f"{branch}/"):
            break
    else:
        raise InternalError("invalid identifier")

    problem = remainder[len(branch)+1:]
    return repo, branch, problem


def prepare_checks(checks_root, reponame, branch, offline=False):
    """If {checks_root} exists, update it and checkout {branch}, else clone it from github.com/{reponame}."""

    if checks_root.exists():
        repo = git.Repo(str(checks_root))
        origin = repo.remotes["origin"]
        try:
            if not offline:
                origin.fetch()
        except git.exc.GitError:
            raise InternalError(f"failed to fetch checks from remote repository")

        try:
            origin.refs[branch].checkout()
        except IndexError:
            raise InternalError(f"no branch {branch} in repository {reponame}")
    elif offline:
        raise InternalError("invalid identifier")
    else:
        try:
            repo = git.Repo.clone_from(f"https://github.com/{reponame}", str(checks_root), branch=branch, depth=1)
        except git.exc.GitError:
            raise InternalError("failed to clone checks")


def install_requirements(*dirs, verbose=False):
    """Look for a requirements.txt in each dir in {dirs} and install it via pip.
    Suppress pip output unless {verbose} is True."""
    stdout = stderr = None if verbose else subprocess.DEVNULL
    for dir in dirs:
        requirements = dir / "requirements.txt"

        if not requirements.exists():
            continue

        pip = ["pip", "install", "-r", str(requirements)]

        # Unless we are in a virtualenv, we need --user
        if not hasattr(sys, "real_prefix") and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            pip.append("--user")

        try:
            subprocess.check_call(pip, stdout=stdout, stderr=stderr)
        except subprocess.CalledProcessError:
            raise InternalError(
                f"failed to install dependencies in ({requirements[len(checks_dir) + 1:]})")


def await_results(url, pings=45, sleep=2):
    """Ping {url} until it returns a results payload, timing out after
    {pings} pings and waiting {sleep} seconds between pings."""

    print("Checking...", end="", flush=True)
    for _ in range(pings):
        # Query for check results.
        res = requests.post(url)
        if res.status_code != 200:
            continue
        payload = res.json()
        if payload["complete"]:
            break
        print(".", end="", flush=True)
        time.sleep(sleep)
    else:
        # Terminate if no response
        print()
        raise InternalError(
            f"check50 is taking longer than normal!\nSee https://cs50.me/checks/{commit_hash} for more detail.")
    print()

    # TODO: Should probably check payload["checks"]["version"] here to make sure major version is same as __version__
    # (otherwise we may not be able to parse results)
    return (CheckResult(**result) for result in payload["checks"]["results"])


def main():
    parser = argparse.ArgumentParser(prog="check50")

    parser.add_argument("identifier")
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--dev",
                        action="store_true",
                        help="run check50 in development mode (implies --offline).\n"
                             "causes IDENTIFIER to be interpreted as a literal path to a checks package")
    parser.add_argument("--offline",
                        action="store_true",
                        help="run checks completely offline (implies --local)")
    parser.add_argument("-l", "--local",
                        action="store_true",
                        help="run checks locally instead of uploading to cs50")
    parser.add_argument("--log",
                        action="store_true",
                        help="display more detailed information about check results")
    parser.add_argument("--repo", "-r",
                        action="store",
                        help="repo to clone checks from")
    parser.add_argument("-o", "--output",
                        action="store",
                        default="ansi",
                        choices=["ansi", "json"],
                        help="format of check results")
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="display the full tracebacks of any errors (also implies --log)")
    parser.add_argument("-V", "--version",
                        action="version",
                        version=f"%(prog)s {__version__}")

    args = parser.parse_args()

    excepthook.verbose = args.verbose

    if not args.files:
        args.files = os.listdir(".")

    if args.verbose:
        # Show all git output in verbose mode.
        # This is supposed to be done by setting the GIT_PYTHON_TRACE env variable,
        # but GitPython checks this once when it is imported, not when it is used.
        # Setting it this way is technically undocumented, but convenient.
        git.Git.GIT_PYTHON_TRACE = "full"
        logging.basicConfig(level=logging.INFO)

        args.log = True

    if args.dev:
        args.offline = True

    if args.offline:
        args.local = True

    if args.local:
        if args.dev:
            internal.check_dir = Path(args.identifier).expanduser().absolute()
        else:
            repo, branch, problem = parse_identifier(args.identifier)
            checks_root = Path(f"~/.local/share/check50/{repo}").expanduser().absolute()
            prepare_checks(checks_root, repo, branch, offline=args.offline)
            internal.check_dir = checks_root / problem.replace("/", os.sep)
            if not args.offline:
                install_requirements(checks_root, internal.check_dir / ".meta50", verbose=args.verbose)


        results = CheckRunner(internal.check_dir / "__init__.py").run(args.files)
    else:
        # TODO: Remove this before we ship
        raise NotImplementedError("cannot run check50 remotely, until version 3.0.0 is shipped ")
        import submit50
        submit50.handler.type = "check"
        signal.signal(signal.SIGINT, submit50.handler)
        submit50.run.verbose = args.verbose
        username, commit_hash = submit50.submit("check50", args.identifier)
        results = await_results(f"https://cs50.me/check50/status/{username}/{commit_hash}")

    if args.output == "json":
        print_json(results)
    else:
        print_ansi(results, log=args.log)


if __name__ == "__main__":
    main()