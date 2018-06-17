import argparse
import importlib
import inspect
import itertools
import json
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
    output = []
    for result in results:
        output.append(attr.asdict(result))
    json.dump(output, sys.stdout, cls=Encoder)


def print_ansi(results, log=False):
    for result in results:
        if result.status is Status.Pass:
            cprint(f":) {result.description}", "green")
        elif result.status is Status.Fail:
            cprint(f":( {result.description}", "red")
            if result.failure.get("rationale") is not None:
                cprint(f"    {result.failure.get('rationale')}", "red")
        elif result.status is Status.Skip:
            cprint(f":| {result.description}", "yellow")
            cprint(f"    {result.failure.get('rationale') or 'check skipped'}", "yellow")

        if log:
            for line in result.log:
                print(f"    {line}")



def prepare_checks(reponame, checks_root, branch, offline=False, verbose=False):
    """If {checks_root}/{repo} exists, update it and checkout {branch}, else clone it from GitHub.
    If offline is False, install any check dependencies from requirements.txt.
    NOTE: internal.check_dir must be initialized before running this function in online mode."""

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

    if not offline:
        install_requirements(checks_root, internal.check_dir / ".meta50", verbose=verbose)


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

    return (CheckResult(**result) for result in payload["checks"])


def apply_config(args):
    """Fill in unspecified command line arguments from the config file.
    Config file is found by finding the longest common path in args.files,
    and traversing upwards until .check50.yaml is found."""
    # Variables to be read from configuration file
    config_vars = ["branch", "repo"]

    unspecified = [var for var in config_vars if getattr(args, var) is None]

    # All config vars were given on the command line, no need to consult config
    if not unspecified:
        return

    # Find configuration file
    config_dir = Path(os.path.commonpath(args.files)).expanduser().absolute()
    for path in itertools.chain((config_dir,), config_dir.parents):
        config_file = path / ".check50.yaml"
        if config_file.exists():
            break
    else:
        raise InternalError(f"could not find configuration file.\nHave you run check50-setup?")

    with open(config_file) as f:
        config = yaml.load(f)

    # Apply config file
    for config_var in unspecified:
        value = config.get(config_var)
        if value is not None:
            setattr(args, config_var, value)
        else:
            raise InternalError(f"missing required argument: {config_var}")


def setup_main():
    """main function for check50-setup"""
    parser = argparse.ArgumentParser(prog="check50-setup")
    parser.add_argument("url", action="store",
                        help="url of check50 configuration file for your course")
    parser.add_argument("directory", action="store",
                        default="~/", type=Path,
                        help="directory in which to store configuration file (defaults to ~/)")
    args = parser.parse_args()

    args.directory = args.directory.expanduser().resolve()

    res = requests.get(url)
    # Maybe we want to do more validation so e.g. setup-checkc50 google.com doesn't work?
    if res.status_code != 200:
        raise InternalError("failed to fetch check50 configuration file")

    if not args.directory.exists():
        args.directory.mkdir(parents=True)

    with open(args.directory / ".check50.yaml") as f:
        f.write(res.text)


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
    parser.add_argument("--branch", "-b",
                        action="store",
                        help="branch to clone checks from")
    parser.add_argument("--repo", "-r",
                        action="store",
                        help="repo to clone checks from 2018")
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
        args.log = True

    # --dev => --offline and disables configuration files
    if args.dev:
        args.offline = True
    else:
        apply_config(args)

    if args.offline:
        args.local = True

    if args.local:
        if not args.dev:
            checks_root = Path(f"~/.local/share/check50/{args.repo}").expanduser().resolve()
            internal.check_dir = checks_root / args.identifier.replace("/", os.sep)
            prepare_checks(args.repo, checks_root, args.branch, offline=args.offline, verbose=args.verbose)
        else:
            internal.check_dir = Path(args.identifier).expanduser().resolve()
        results = CheckRunner(internal.check_dir / "__init__.py").run(args.files)
    else:
        raise NotImplementedError("cannot run check50 remotely, until version 3.0.0 is shipped ")
        import submit50
        submit50.handler.type = "check"
        signal.signal(signal.SIGINT, submit50.handler)
        submit50.run.verbose = args.verbose
        full_identifier = "|".join((args.repo, args.branch, args.identifier))
        username, commit_hash = submit50.submit("check50", full_identifier)
        results = await_results(f"https://cs50.me/check50/status/{username}/{commit_hash}")

    if args.output == "json":
        print_json(results)
    else:
        print_ansi(results, log=args.log)


if __name__ == "__main__":
    main()
