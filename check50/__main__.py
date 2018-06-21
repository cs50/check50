import argparse
import contextlib
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
import yaml

from . import internal, __version__
from .api import Failure
from .runner import CheckRunner, Status, CheckResult
from . import compiler


class InternalError(Exception):
    """Error during execution of check50."""

    def __init__(self, msg):
        self.msg = msg


class InvalidIdentifier(InternalError):
    def __init__(self, identifier=None):
        self.identifier = identifier
        super().__init__(f"invalid identifier{f': {identifier}' if identifier else ''}")


def excepthook(cls, exc, tb):
    if issubclass(cls, InternalError):
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
    json.dump({"results": {name: attr.asdict(result) for name, result in results.items()},
               "version": __version__},
              sys.stdout, cls=Encoder)


def print_ansi(results, log=False):
    for result in results.values():
        if result.status is Status.Pass:
            cprint(f":) {result.description}", "green")
        elif result.status is Status.Fail:
            cprint(f":( {result.description}", "red")
            if result.why.get("rationale") is not None:
                cprint(f"    {result.why['rationale']}", "red")
            if result.why.get("help") is not None:
                cprint(f"    {result.why['help']}", "red")
        elif result.status is Status.Skip:
            cprint(f":| {result.description}", "yellow")
            cprint(f"    {result.why.get('rationale') or 'check skipped'}", "yellow")

        if log:
            for line in result.log:
                print(f"    {line}")


def parse_identifier(identifier, offline=False):
    # Find second "/" in identifier
    idx = identifier.find("/", identifier.find("/") + 1)
    if idx == -1:
        raise InvalidIdentifier(identifier)

    repo, remainder = identifier[:idx], identifier[idx+1:]

    try:
        if offline:
            branches = map(str, git.Repo(f"~/.local/share/check50/{repo}").branches)
        else:
            branches = (line.split("\t")[1].replace("refs/heads/", "")
                        for line in git.Git().ls_remote(f"https://github.com/{repo}", heads=True).split("\n"))
    except git.GitError:
        raise InvalidIdentifier(identifier)

    for branch in branches:
        if remainder.startswith(f"{branch}/"):
            break
    else:
        raise InvalidIdentifier(identifier)

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
        origin.refs[branch].checkout()
    elif offline:
        raise InvalidIdentifier()
    else:
        try:
            repo = git.Repo.clone_from(
                f"https://github.com/{reponame}", str(checks_root), branch=branch, depth=1)
        except git.exc.GitError:
            raise InternalError("failed to clone checks")


def install_requirements(requirements, verbose=False):
    """Look for a requirements.txt in each dir in {dirs} and install it via pip.
    Suppress pip output unless {verbose} is True."""

    stdout = stderr = None if verbose else subprocess.DEVNULL

    requirements = Path(requirements).expanduser().absolute()

    if not requirements.exists():
        raise FileNotFoundError(requirements)

    pip = ["pip", "install", "-r", requirements]

    # Unless we are in a virtualenv, we need --user
    if sys.base_prefix == sys.prefix and not hasattr(sys, "real_prefix"):
        pip.append("--user")

    try:
        subprocess.check_call(pip, stdout=stdout, stderr=stderr)
    except subprocess.CalledProcessError:
        raise InternalError(
            f"failed to install dependencies from {requirements}")


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


def parse_config(check_dir):
    config_file = check_dir / ".check50.yaml"

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        raise InvalidIdentifier()

    options = {
        "checks": "__init__.py",
        "requirements": False,
        "locale": False,
    }

    if config is not None:
        options.update(config)


    if isinstance(options["checks"], dict):
        check = compiler.compile(options["checks"])
        with open(check_dir / "__init__.py", "w") as f:
            f.write(compiler.compile(options["checks"]))
        options["checks"] = "__init__.py"

    return options


def main():
    parser = argparse.ArgumentParser(prog="check50")

    parser.add_argument("identifier")
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--dev",
                        action="store_true",
                        help="run check50 in development mode (implies --offline and --verbose).\n"
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

    if not args.files:
        args.files = os.listdir(".")

    if args.dev:
        args.offline = True
        args.verbose = True

    if args.offline:
        args.local = True

    if args.verbose:
        # Show all git output in verbose mode.
        # This is supposed to be done by setting the GIT_PYTHON_TRACE env variable,
        # but GitPython checks this once when it is imported, not when it is used.
        # Setting it this way is technically undocumented, but convenient.
        git.Git.GIT_PYTHON_TRACE = "full"
        logging.basicConfig(level=logging.INFO)
        args.log = True

    excepthook.verbose = args.verbose

    if args.local:
        if args.dev:
            internal.check_dir = Path(args.identifier).expanduser().absolute()
        else:
            repo, branch, problem = parse_identifier(args.identifier, offline=args.offline)
            checks_root = Path(f"~/.local/share/check50/{repo}").expanduser().absolute()
            prepare_checks(checks_root, repo, branch, offline=args.offline)
            internal.check_dir = checks_root / problem.replace("/", os.sep)

        options = parse_config(internal.check_dir)

        if not args.offline and options["requirements"]:
            install_requirements(internal.check_dir / options["requirements"], verbose=args.verbose)

        checks_file = (internal.check_dir / options["checks"]).absolute()

        with contextlib.redirect_stdout(sys.stdout if args.verbose else open(os.devnull, "w")):
            results = CheckRunner(checks_file, locale=options["locale"]).run(args.files)
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
