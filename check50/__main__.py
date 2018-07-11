import push50
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
from pexpect.exceptions import EOF
import requests
from termcolor import cprint
import yaml

from . import internal, __version__, simple
from .api import Failure
from .runner import CheckRunner, Status, CheckResult

push50.LOCAL_PATH = "~/.local/share/check50"


class Error(Exception):
    pass


def excepthook(cls, exc, tb):
    if (issubclass(cls, Error) or issubclass(cls, push50.Error)) and exc.args:
        cprint(str(exc), "red", file=sys.stderr)
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

def install_dependencies(dependencies, verbose=False):
    """Install all packages in dependency list via pip"""

    if not dependencies:
        return

    stdout = stderr = None if verbose else subprocess.DEVNULL
    with tempfile.NamedTemporaryFile() as req_file:
        req_file.writelines(dependencies)
        pip = ["pip", "install", "-r", req_file.name]
        # Unless we are in a virtualenv, we need --user
        if sys.base_prefix == sys.prefix and not hasattr(sys, "real_prefix"):
            pip.append("--user")

        try:
            subprocess.check_call(pip, stdout=stdout, stderr=stderr)
        except subprocess.CalledProcessError:
            raise Error(f"failed to install dependencies from {dependencies}")


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
        raise Error(f"check50 is taking longer than normal!\nSee https://cs50.me/checks/{commit_hash} for more detail.")
    print()

    # TODO: Should probably check payload["checks"]["version"] here to make sure major version is same as __version__
    # (otherwise we may not be able to parse results)
    return (CheckResult(**result) for result in payload["checks"]["results"])


def main():
    parser = argparse.ArgumentParser(prog="check50")

    parser.add_argument("slug", help="a slug identifying a check50 problem in the form of <org>/<repo>/<branch>/<problem>")
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--dev",
                        action="store_true",
                        help="run check50 in development mode (implies --offline and --verbose).\n"
                             "causes SLUG to be interpreted as a literal path to a checks package")
    parser.add_argument("--offline",
                        action="store_true",
                        help="run checks completely offline (implies --local)")
    parser.add_argument("-l", "--local",
                        action="store_true",
                        help="run checks locally instead of uploading to cs50 (enabled by default in beta version)")
    parser.add_argument("--log",
                        action="store_true",
                        help="display more detailed information about check results")
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

    # TODO: remove this when submit.cs50.io API is stabilized
    args.local = True

    if not args.files:
        args.files = os.listdir(".")

    if args.dev:
        args.offline = True
        args.verbose = True

    if args.offline:
        args.local = True

    if args.verbose:
        # Show push50 commands being run in verbose mode
        logging.basicConfig(level="INFO")
        push50.ProgressBar.DISABLED = True
        args.log = True

    excepthook.verbose = args.verbose

    if args.local:
        # if developing, assume slug is a path to check_dir
        if args.dev:
            internal.check_dir = Path(args.slug).expanduser().absolute()
            with open(internal.check_dir / ".cs50.yaml") as f:
                config = yaml.safe_load(f.read()).get("check50", False)
            if not config:
                raise Error(f"check50 has not been enabled for this identifier. "
                             "Ensure that {internal.check_dir / 'cs50.yaml'} contains "
                             " a 'check50' key.")
        # otherwise have push50 create a local copy of slug
        else:
            import pdb; pdb.set_trace()
            internal.check_dir, config = push50.local(args.slug, "check50", offline=args.offline)

        config = internal.apply_default_config(config)

        if not args.offline:
            install_dependencies(config["dependencies"], verbose=args.verbose)

        checks_file = (internal.check_dir / config["checks"]).absolute()

        with contextlib.redirect_stdout(sys.stdout if args.verbose else open(os.devnull, "w")):
            results = CheckRunner(checks_file, locale=config["locale"]).run(args.files)
    else:
        # TODO: Remove this before we ship
        raise NotImplementedError("cannot run check50 remotely, until version 3.0.0 is shipped ")
        username, commit_hash = push50.push(org="check50", slug=args.slug, tool="check50")
        results = await_results(f"https://cs50.me/check50/status/{username}/{commit_hash}")

    if args.output == "json":
        print_json(results)
    else:
        print_ansi(results, log=args.log)


if __name__ == "__main__":
    main()
