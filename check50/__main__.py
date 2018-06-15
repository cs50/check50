import signal
import os
import subprocess
import importlib
import json
import sys
import argparse
import tempfile
import shutil
import errno
import inspect
import traceback

from pprint import pprint
from pathlib import Path

import attr
from termcolor import cprint

from pexpect.exceptions import EOF

from . import internal, __version__
from .api import Failure
from .runner import CheckRunner, check_names, Status


class InternalError(Exception):
    """Error during execution of check50."""

    def __init__(self, msg):
        self.msg = msg


class Encoder(json.JSONEncoder):
    """Custom class for JSON encoding."""

    def default(self, o):
        if o == EOF:
            return "EOF"
        elif isinstance(o, Status):
            return o.value

        return o.__dict__


def handler(number, frame):
    cprint("Check cancelled.", "red")
    sys.exit(1)


def excepthook(cls, exc, tb):
    # Class is a BaseException, better just quit.
    if not issubclass(cls, Exception):
        print()
        return

    if cls is InternalError:
        cprint(exc.msg, "red", file=sys.stderr)
    elif cls is FileNotFoundError:
        cprint(f"{exc.filename} not found", "red", file=sys.stderr)
    else:
        cprint("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!", "red", file=sys.stderr)

    if main.args.debug:
        traceback.print_exception(cls, exc, tb)

    sys.exit(1)


sys.excepthook = excepthook


def print_ansi(results, log=False):
    for result in results:
        if result.status is Status.Pass:
            cprint(f":) {result.description}", "green")
        elif result.status is Status.Fail:
            cprint(f":( {result.description}", "red")
            if result.error.get("rationale") is not None:
                cprint(f"    {result.error.get('rationale')}", "red")
        elif result.status is Status.Skip:
            cprint(f":| {result.description}", "yellow")
            cprint(f"    {result.error.get('rationale') or 'check skipped'}", "yellow")

        if log:
            for line in result.log:
                print(f"    {line}")


def parse_identifier(identifier):
    try:
        slug, repo = identifier.split("@")
    except ValueError:
        slug, repo = identifier, "cs50/checks"

    try:
        org, repo = repo.split("/")
    except ValueError:
        raise InternalError(
            f"expected repository to be of the form username/repository, but got \"{repo}\"")

    return slug, org, repo


def clone_checks(org, repo, checks_root):
    if os.path.exists(checks_root):
        command = ["git", "-C", checks_root, "pull", "origin", "master"]
    else:
        command = ["git", "clone", f"https://github.com/{org}/{repo}", checks_root]

    stdout = stderr = None if main.args.debug else subprocess.DEVNULL

    # Update checks via git.
    try:
        subprocess.check_call(command, stdout=stdout, stderr=stderr)
    except subprocess.CalledProcessError:
        raise InternalError("failed to clone checks")


def install_requirements(*dirs):
    for dir in dirs:
        requirements = os.path.join(dir, "requirements.txt")
        if os.path.exists(requirements):
            pip = ["pip", "install", "-r", requirements]

            # If we are not in a virtualenv, we need --user
            if not hasattr(sys, "real_prefix") and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
                pip.append("--user")

            try:
                subprocess.check_call(pip, stdout=stdout, stderr=stderr)
            except subprocess.CalledProcessError:
                raise InternalError("failed to install dependencies in ({})".format(
                    requirements[len(checks_dir) + 1:]))


def run_submit50(identifier, debug=False):
    import submit50
    submit50.handler.type = "check"
    signal.signal(signal.SIGINT, submit50.handler)

    submit50.run.verbose = debug
    username, commit_hash = submit50.submit("check50", identifier)

    # Wait until payload comes back with check data.
    print("Checking...", end="")
    sys.stdout.flush()
    while pings <= 45:
        pings += 1

        # Query for check results.
        res = requests.post(f"https://cs50.me/check50/status/{username}/{commit_hash}")
        if res.status_code != 200:
            continue
        payload = res.json()
        if payload["complete"]:
            break
        print(".", end="")
        sys.stdout.flush()
        time.sleep(2)
    else:
        # Terminate if no response
        print()
        raise InternalError(f"check50 is taking longer than normal!\nSee https://cs50.me/checks/{commit_hash} for more detail.")

    print()
    return payload["checks"], commit_hash


def print_json(results):
    output = []
    for result in results:
        output.append(attr.asdict(result))
    json.dump(output, sys.stdout, cls=Encoder)


def main():
    signal.signal(signal.SIGINT, handler)

    # Parse command line arguments.
    parser = argparse.ArgumentParser(prog="check50")
    parser.add_argument("identifier")
    parser.add_argument("files", nargs="*", default=os.listdir("."))
    parser.add_argument("-j", "--json",
                        action="store_true",
                        help="display machine-readable JSON output")
    parser.add_argument("-l", "--local",
                        action="store_true",
                        help="run checks locally instead of uploading to cs50")
    parser.add_argument("--offline",
                        action="store_true",
                        help="run checks completely offline (implies --local)")
    parser.add_argument("--checkdir",
                        action="store",
                        default="~/.local/share/check50",
                        help="specify directory containing the checks "
                             "(~/.local/share/check50 by default)")
    parser.add_argument("--log",
                        action="store_true",
                        help="display more detailed information about check results")
    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="display the full tracebacks of any errors (also implies --log)")
    parser.add_argument("-v", "--version", action="version",
                        version=f"%(prog)s {__version__}")
    parser.add_argument("--output", "-o", action="store", default="ansi", choices=["ansi", "json"])

    main.args = parser.parse_args()
    main.args.checkdir = os.path.abspath(os.path.expanduser(main.args.checkdir))

    if main.args.offline:
        main.args.local = True

    if main.args.debug:
        main.args.log = True

    if main.args.local:
        slug, org, repo = parse_identifier(main.args.identifier)
        checks_root = Path(main.args.checkdir) / org / repo
        internal.check_dir = checks_root / slug.replace("/", os.sep)
        if not main.args.offline:
            clone_checks(org, repo, checks_root)
            install_requirements(checks_root, check_dir / ".meta50")
        results = CheckRunner(slug, internal.check_dir / "__init__.py").run(main.args.files)
    else:
        results, commit_hash = run_submit50(main.args.identifier, main.args.debug)

    if main.args.output == "json":
        print_json(results.values())
    else:
        print_ansi(results.values(), main.args.log)

    if not main.args.local:
        print(f"See https://cs50.me/checks/{commit_hash} for more detail.")

if __name__ == "__main__":
    main()
