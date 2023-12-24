import argparse
import contextlib
import enum
import gettext
import importlib
import inspect
import itertools
from json import JSONDecodeError
import logging
import os
import platform
import site
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

import attr
import lib50
import requests
import termcolor

from . import _exceptions, internal, renderer, __version__
from .contextmanagers import nullcontext
from .runner import CheckRunner

LOGGER = logging.getLogger("check50")

lib50.set_local_path(os.environ.get("CHECK50_PATH", "~/.local/share/check50"))


class LogLevel(enum.IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "ERROR": "red",
        "WARNING": "yellow",
        "DEBUG": "cyan",
        "INFO": "magenta",
    }

    def __init__(self, fmt, use_color=True):
        super().__init__(fmt=fmt)
        self.use_color = use_color

    def format(self, record):
        msg = super().format(record)
        return msg if not self.use_color else termcolor.colored(msg, getattr(record, "color", self.COLORS.get(record.levelname)))


_exceptions.ExceptHook.initialize()


def install_dependencies(dependencies):
    """Install all packages in dependency list via pip."""
    if not dependencies:
        return

    with tempfile.TemporaryDirectory() as req_dir:
        req_file = Path(req_dir) / "requirements.txt"

        with open(req_file, "w") as f:
            for dependency in dependencies:
                f.write(f"{dependency}\n")

        pip = [sys.executable or "python3", "-m", "pip", "install", "-r", req_file]
        # Unless we are in a virtualenv, we need --user
        if sys.base_prefix == sys.prefix and not hasattr(sys, "real_prefix"):
            pip.append("--user")

        try:
            output = subprocess.check_output(pip, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            raise _exceptions.Error(_("failed to install dependencies"))

        LOGGER.info(output)

        # Reload sys.path, to find recently installed packages
        importlib.reload(site)


def install_translations(config):
    """Add check translations according to ``config`` as a fallback to existing translations"""

    if not config:
        return

    from . import _translation
    checks_translation = gettext.translation(domain=config["domain"],
                                             localedir=internal.check_dir / config["localedir"],
                                             fallback=True)
    _translation.add_fallback(checks_translation)


def compile_checks(checks, prompt=False):
    # Prompt to replace __init__.py (compile destination)
    if prompt and os.path.exists(internal.check_dir / "__init__.py"):
        if not internal._yes_no_prompt("check50 will compile the YAML checks to __init__.py, are you sure you want to overwrite its contents?"):
            raise Error("Aborting: could not overwrite to __init__.py")

    # Compile simple checks
    with open(internal.check_dir / "__init__.py", "w") as f:
        f.write(simple.compile(checks))

    return "__init__.py"


def setup_logging(level):
    """
    Sets up logging for lib50.
    level 'info' logs all git commands run to stderr
    level 'debug' logs all git commands and their output to stderr
    """

    for logger in (logging.getLogger("lib50"), LOGGER):
        # Set verbosity level on the lib50 logger
        logger.setLevel(level.upper())

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(ColoredFormatter("(%(levelname)s) %(message)s", use_color=sys.stderr.isatty()))

        # Direct all logs to sys.stderr
        logger.addHandler(handler)

    # Don't animate the progressbar if LogLevel is either info or debug
    lib50.ProgressBar.DISABLED = logger.level < LogLevel.WARNING


def await_results(commit_hash, slug, pings=45, sleep=2):
    """
    Ping {url} until it returns a results payload, timing out after
    {pings} pings and waiting {sleep} seconds between pings.
    """

    try:
        for _i in range(pings):
            # Query for check results.
            res = requests.get(f"https://submit.cs50.io/api/results/check50", params={"commit_hash": commit_hash, "slug": slug})
            results = res.json()

            if res.status_code not in [404, 200]:
                raise _exceptions.RemoteCheckError(results)

            if res.status_code == 200 and results["received_at"] is not None:
                break
            time.sleep(sleep)
        else:
            # Terminate if no response
            raise _exceptions.Error(
                _("check50 is taking longer than normal!\n"
                "See https://submit.cs50.io/check50/{} for more detail").format(commit_hash))

    except JSONDecodeError:
        # Invalid JSON object received from submit.cs50.io
        raise _exceptions.Error(
            _("Sorry, something's wrong, please try again.\n"
            "If the problem persists, please visit our status page https://cs50.statuspage.io for more information."))

    if not results["check50"]:
        raise _exceptions.RemoteCheckError(results)

    if "error" in results["check50"]:
        raise _exceptions.RemoteCheckError(results["check50"])

    # TODO: Should probably check payload["version"] here to make sure major version is same as __version__
    # (otherwise we may not be able to parse results)
    return results["tag_hash"], {
        "slug": results["check50"]["slug"],
        "results": results["check50"]["results"],
        "version": results["check50"]["version"]
    }


class LogoutAction(argparse.Action):
    """Hook into argparse to allow a logout flag"""

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, help=_("logout of check50")):
        super().__init__(option_strings, dest=dest, nargs=0, default=default, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            lib50.logout()
        except lib50.Error:
            raise _exceptions.Error(_("failed to logout"))
        else:
            termcolor.cprint(_("logged out successfully"), "green")
        parser.exit()


def raise_invalid_slug(slug, offline=False):
    """Raise an error signalling slug is invalid for check50."""
    msg = _("Could not find checks for {}.").format(slug)

    similar_slugs = lib50.get_local_slugs("check50", similar_to=slug)[:3]
    if similar_slugs:
        msg += _(" Did you mean:")
        for similar_slug in similar_slugs:
            msg += f"\n    {similar_slug}"
        msg += _("\nDo refer back to the problem specification if unsure.")

    if offline:
        msg += _("\nIf you are confident the slug is correct and you have an internet connection," \
                " try running without --offline.")

    raise _exceptions.Error(msg)


def process_args(args):
    """Validate arguments and apply defaults that are dependent on other arguments"""

    # dev implies offline, verbose, and log level "INFO" if not overwritten
    if args.dev:
        args.offline = True
        if "ansi" in args.output:
            args.ansi_log = True

        if not args.log_level:
            args.log_level = "info"

    # offline implies local
    if args.offline:
        args.no_install_dependencies = True
        args.no_download_checks = True
        args.local = True

    if not args.log_level:
        args.log_level = "warning"

    # Setup logging for lib50
    setup_logging(args.log_level)

    # Warning in case of running remotely with no_download_checks or no_install_dependencies set
    if not args.local:
        useless_args = []
        if args.no_download_checks:
            useless_args.append("--no-downloads-checks")
        if args.no_install_dependencies:
            useless_args.append("--no-install-dependencies")

        if useless_args:
            LOGGER.warning(_("You should always use --local when using: {}").format(", ".join(useless_args)))

    # Filter out any duplicates from args.output
    seen_output = []
    for output in args.output:
        if output in seen_output:
            LOGGER.warning(_("Duplicate output format specified: {}").format(output))
        else:
            seen_output.append(output)

    args.output = seen_output

    if args.ansi_log and "ansi" not in seen_output:
        LOGGER.warning(_("--ansi-log has no effect when ansi is not among the output formats"))


class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message != "\n":
            self.logger.log(self.level, message)

    def flush(self):
        pass


def main():
    parser = argparse.ArgumentParser(prog="check50", formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("slug", help=_("prescribed identifier of work to check"))
    parser.add_argument("-d", "--dev",
                        action="store_true",
                        help=_("run check50 in development mode (implies --offline, and --log-level info).\n"
                               "causes slug to be interpreted as a literal path to a checks package."))
    parser.add_argument("--offline",
                        action="store_true",
                        help=_("run checks completely offline (implies --local, --no-download-checks and --no-install-dependencies)"))
    parser.add_argument("-l", "--local",
                        action="store_true",
                        help=_("run checks locally instead of uploading to cs50"))
    parser.add_argument("-o", "--output",
                        action="store",
                        nargs="+",
                        default=["ansi", "html"],
                        choices=["ansi", "json", "html"],
                        help=_("format of check results"))
    parser.add_argument("--target",
                        action="store",
                        nargs="+",
                        help=_("target specific checks to run"))
    parser.add_argument("--output-file",
                        action="store",
                        metavar="FILE",
                        help=_("file to write output to"))
    parser.add_argument("--log-level",
                        action="store",
                        choices=[level.name.lower() for level in LogLevel],
                        type=str.lower,
                        help=_('warning: displays usage warnings.'
                               '\ninfo: adds all commands run, any locally installed dependencies and print messages.'
                               '\ndebug: adds the output of all commands run.'))
    parser.add_argument("--ansi-log",
                        action="store_true",
                        help=_("display log in ansi output mode"))
    parser.add_argument("--no-download-checks",
                        action="store_true",
                        help=_("do not download checks, but use previously downloaded checks instead (only works with --local)"))
    parser.add_argument("--no-install-dependencies",
                        action="store_true",
                        help=_("do not install dependencies (only works with --local)"))
    parser.add_argument("-V", "--version",
                        action="version",
                        version=f"%(prog)s {__version__}")
    parser.add_argument("--logout", action=LogoutAction)

    args = parser.parse_args()

    internal.slug = args.slug

    # Validate arguments and apply defaults
    process_args(args)

    # Set excepthook
    _exceptions.ExceptHook.initialize(args.output, args.output_file)

    # If remote, push files to GitHub and await results
    if not args.local:
        commit_hash = lib50.push("check50", internal.slug, internal.CONFIG_LOADER, data={"check50": True})[1]
        with lib50.ProgressBar("Waiting for results") if "ansi" in args.output else nullcontext():
            tag_hash, results = await_results(commit_hash, internal.slug)

    # Otherwise run checks locally
    else:
        with lib50.ProgressBar("Checking") if "ansi" in args.output else nullcontext():
            # If developing, assume slug is a path to check_dir
            if args.dev:
                internal.check_dir = Path(internal.slug).expanduser().resolve()
                if not internal.check_dir.is_dir():
                    raise _exceptions.Error(_("{} is not a directory").format(internal.check_dir))
            # Otherwise have lib50 create a local copy of slug
            else:
                try:
                    internal.check_dir = lib50.local(internal.slug, offline=args.no_download_checks)
                except lib50.ConnectionError:
                    raise _exceptions.Error(_("check50 could not retrieve checks from GitHub. Try running check50 again with --offline.").format(internal.slug))
                except lib50.InvalidSlugError:
                    raise_invalid_slug(internal.slug, offline=args.no_download_checks)

            # Load config
            config = internal.load_config(internal.check_dir)

            # Compile local checks if necessary
            if isinstance(config["checks"], dict):
                config["checks"] = internal.compile_checks(config["checks"], prompt=args.dev)

            install_translations(config["translations"])

            if not args.no_install_dependencies:
                install_dependencies(config["dependencies"])

            checks_file = (internal.check_dir / config["checks"]).resolve()

            # Have lib50 decide which files to include
            included_files = lib50.files(config.get("files"))[0]

            # Create a working_area (temp dir) named - with all included student files
            with CheckRunner(checks_file, included_files) as check_runner, \
                    contextlib.redirect_stdout(LoggerWriter(LOGGER, logging.NOTSET)), \
                    contextlib.redirect_stderr(LoggerWriter(LOGGER, logging.NOTSET)):

                check_results = check_runner.run(args.target)
                results = {
                    "slug": internal.slug,
                    "results": [attr.asdict(result) for result in check_results],
                    "version": __version__
                }

    LOGGER.debug(results)

    # Render output
    file_manager = open(args.output_file, "w") if args.output_file else nullcontext(sys.stdout)
    with file_manager as output_file:
        for output in args.output:
            if output == "json":
                output_file.write(renderer.to_json(**results))
                output_file.write("\n")
            elif output == "ansi":
                output_file.write(renderer.to_ansi(**results, _log=args.ansi_log))
                output_file.write("\n")
            elif output == "html":
                if os.environ.get("CS50_IDE_TYPE") and args.local:
                    html = renderer.to_html(**results)
                    subprocess.check_call(["c9", "exec", "renderresults", "check50", html])
                else:
                    if args.local:
                        html = renderer.to_html(**results)
                        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as html_file:
                            html_file.write(html)

                        if "microsoft-standard" in platform.uname().release:
                            stream = os.popen(f"wslpath -m {html_file.name}")
                            wsl_path = stream.read().strip()
                            url = f"file://{wsl_path}"
                        else:
                            url = f"file://{html_file.name}"
                    else:
                        url = f"https://submit.cs50.io/check50/{tag_hash}"

                    termcolor.cprint(_("To see more detailed results go to {}").format(url), "white", attrs=["bold"])

    sys.exit(should_fail(results))

def should_fail(results):
    return "error" in results or any(not result["passed"] for result in results["results"])


if __name__ == "__main__":
    main()
