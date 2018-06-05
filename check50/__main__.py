import signal
import config
import os
import subprocess
import imp
import termcolor
import sys
import argparse
import tempfile
import shutil
import errno
import inspect
from errors import Error, InternalError

_rootPath = os.sep.join(os.path.abspath(os.path.dirname(__file__)).split(os.sep)[:-1])
if _rootPath not in sys.path:
	sys.path.append(_rootPath)

def handler(number, frame):
    termcolor.cprint("Check cancelled.", "red")
    sys.exit(1)

def copy(src, dst):
    """Copy src to dst, copying recursively if src is a directory"""
    try:
        shutil.copytree(src, os.path.join(dst, os.path.basename(src)))
    except (OSError, IOError) as e:
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else:
            raise

def import_checks(identifier):
    """
    Given an identifier of the form path/to/check@org/repo, clone
    the checks from github.com/org/repo (defaulting to cs50/checks
    if there is no @) into config.args.checkdir. Then extract child
    of Check class from path/to/check/check50/__init__.py and return it

    Throws ImportError on error
    """
    if not config.args.offline:
        try:
            slug, repo = identifier.split("@")
        except ValueError:
            slug, repo = identifier, "cs50/checks"

        try:
            org, repo = repo.split("/")
        except ValueError:
            raise InternalError(
                "expected repository to be of the form username/repository, but got \"{}\"".format(repo))

        checks_root = os.path.join(config.args.checkdir, org, repo)
        config.check_dir = os.path.join(checks_root, slug.replace("/", os.sep), "check50")

        if os.path.exists(checks_root):
            command = ["git", "-C", checks_root, "pull", "origin", "master"]
        else:
            command = ["git", "clone", "https://github.com/{}/{}".format(org, repo), checks_root]

        # Can't use subprocess.DEVNULL because it requires python 3.3.
        stdout = stderr = None if config.args.verbose else open(os.devnull, "wb")

        # Update checks via git.
        try:
            subprocess.check_call(command, stdout=stdout, stderr=stderr)
        except subprocess.CalledProcessError:
            raise InternalError("failed to clone checks")
    else:
        slug = os.path.join(config.args.checkdir, identifier)
        checks_root = slug
        config.check_dir = os.path.join(checks_root, slug.replace("/", os.sep), "check50")

    # Install any dependencies from requirements.txt either in the root of the
    # repository or in the directory of the specific check.
    for dir in [checks_root, os.path.dirname(config.check_dir)]:
        requirements = os.path.join(dir, "requirements.txt")
        if os.path.exists(requirements):
            args = ["install", "-r", requirements]
            # If we are not in a virtualenv, we need --user
            if not hasattr(sys, "real_prefix"):
                args.append("--user")

            if not config.args.verbose:
                args += ["--quiet"] * 3

            try:
                code = __import__("pip").main(args)
            except SystemExit as e:
                code = e.code

            if code:
                raise InternalError("failed to install dependencies in ({})".format(
                    requirements[len(config.args.checkdir) + 1:]))

    try:
        # Import module from file path directly.
        module = imp.load_source(slug, os.path.join(config.check_dir, "__init__.py"))
        # TODO check for sentinel
        checks = [func for _, func in inspect.getmembers(module, inspect.isfunction) if hasattr(func, "_checks_sentinel")]
    except (OSError, IOError) as e:
        if e.errno != errno.ENOENT:
            raise
    except ValueError as e:
        pass
    else:
        return checks

    raise InternalError("invalid identifier")

def main():
    signal.signal(signal.SIGINT, handler)

    # Parse command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("identifier", nargs=1)
    parser.add_argument("files", nargs="*")
    parser.add_argument("-d", "--debug",
                        action="store_true",
                        help="display machine-readable output")
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
    parser.add_argument("-v", "--verbose",
                        action="store_true",
                        help="display the full tracebacks of any errors")

    config.args = parser.parse_args()
    config.args.checkdir = os.path.abspath(os.path.expanduser(config.args.checkdir))
    identifier = config.args.identifier[0]
    files = config.args.files

    if config.args.offline:
        config.args.local = True

    # Copy all files to temporary directory.
    config.tempdir = tempfile.mkdtemp()
    src_dir = os.path.join(config.tempdir, "_")
    os.mkdir(src_dir)
    if len(files) == 0:
        files = os.listdir(".")
    for filename in files:
        copy(filename, src_dir)

    checks = import_checks(identifier)

    import check50.internal_api

    # TODO sort checks on dependencies

    # TODO multiprocessing kicks in here
    for check in checks:
        check50.internal_api.before()
        check()
        check50.internal_api.after()
    print(check50.internal_api.log_as_str())

    # Get list of results from TestResult class.
    # results = result.results

    # Print the results.
    #if config.args.debug:
    #    print_json(results)
    #else:
    #    print_results(results, log=config.args.log)

main()
