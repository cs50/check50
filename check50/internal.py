"""
Additional check50 internals exposed to extension writers in addition to the standard API
"""

from pathlib import Path
import importlib
import json
import sys
import termcolor
import traceback

import lib50

from . import _simple, __version__

#: Directory containing the check and its associated files
check_dir = None

#: Temporary directory in which check is being run
run_dir = None

#: Boolean that indicates if a check is currently running
check_running = False

#: The user specified slug used to indentifies the set of checks
slug = None

#: ``lib50`` config loader
CONFIG_LOADER = lib50.config.Loader("check50")
CONFIG_LOADER.scope("files", "include", "exclude", "require")


class Error(Exception):
    """Exception for internal check50 errors."""
    pass


class Register:
    """
    Class with which functions can be registered to run before / after checks.
    :data:`check50.internal.register` should be the sole instance of this class.
    """
    def __init__(self):
        self._before_everies = []
        self._after_everies = []
        self._after_checks = []

    def after_check(self, func):
        """Run func once at the end of the check, then discard func.

        :param func: callback to run after check
        :raises check50.internal.Error: if called when no check is being run"""
        if not check_running:
            raise Error("cannot register callback to run after check when no check is running")
        self._after_checks.append(func)

    def after_every(self, func):
        """Run func at the end of every check.

        :param func: callback to be run after every check
        :raises check50.internal.Error: if called when a check is being run"""
        if check_running:
            raise Error("cannot register callback to run after every check when check is running")
        self._after_everies.append(func)

    def before_every(self, func):
        """Run func at the start of every check.

        :param func: callback to be run before every check
        :raises check50.internal.Error: if called when a check is being run"""

        if check_running:
            raise Error("cannot register callback to run before every check when check is running")
        self._before_everies.append(func)

    def __enter__(self):
        for f in self._before_everies:
            f()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Only run 'afters' when check has passed
        if exc_type is not None:
            return

        # Run and remove all checks registered to run after a single check
        while self._after_checks:
            self._after_checks.pop()()

        for f in self._after_everies:
            f()


#: Sole instance of the :class:`check50.internal.Register` class
register = Register()


def excepthook(cls, exc, tb):
    """
    check50's excepthook with configurable error output.

    :ivar excepthook.verbose: show the full tracebook iff set to True
    :vartype excepthook.verbose: bool
    :ivar excepthook.outputs: in which format errors should be returned (can be multiple)
    :vartype excepthook.outputs: tuple of strings, any of "json", "ansi", "html"
    :ivar excepthook.output_file: file to which the output should be redirected
    :vartype excepthook.output_file: str or pathlib.Path

    See also: https://docs.python.org/3/library/sys.html#sys.excepthook
    """

    # All channels to output to
    outputs = excepthook.outputs

    for output in excepthook.outputs:
        outputs.remove(output)
        if output == "json":
            ctxmanager = open(excepthook.output_file, "w") if excepthook.output_file else nullcontext(sys.stdout)
            with ctxmanager as output_file:
                json.dump({
                    "slug": slug,
                    "error": {
                        "type": cls.__name__,
                        "value": str(exc),
                        "traceback": traceback.format_tb(exc.__traceback__),
                        "data" : exc.payload if hasattr(exc, "payload") else {}
                    },
                    "version": __version__
                }, output_file, indent=4)
                output_file.write("\n")

        elif output == "ansi" or output == "html":
            if (issubclass(cls, Error) or issubclass(cls, lib50.Error)) and exc.args:
                termcolor.cprint(str(exc), "red", file=sys.stderr)
            elif issubclass(cls, FileNotFoundError):
                termcolor.cprint(_("{} not found").format(exc.filename), "red", file=sys.stderr)
            elif issubclass(cls, KeyboardInterrupt):
                termcolor.cprint(f"check cancelled", "red")
            elif not issubclass(cls, Exception):
                # Class is some other BaseException, better just let it go
                return
            else:
                termcolor.cprint(_("Sorry, something's wrong! Let sysadmins@cs50.harvard.edu know!"), "red", file=sys.stderr)

            if excepthook.verbose:
                traceback.print_exception(cls, exc, tb)
                if hasattr(exc, "payload"):
                    print("Exception payload:", json.dumps(exc.payload), sep="\n")

    sys.exit(1)


def load_config(check_dir):
    """
    Load configuration file from ``check_dir / ".cs50.yaml"``, applying
    defaults to unspecified values.

    :param check_dir: directory from which to load config file
    :type check_dir: str / Path
    :rtype: dict
    """

    # Defaults for top-level keys
    options = {
        "checks": "__init__.py",
        "dependencies": None,
        "translations": None
    }

    # Defaults for translation keys
    translation_options = {
        "localedir": "locale",
        "domain": "messages",
    }

    # Get config file
    try:
        config_file = lib50.config.get_config_filepath(check_dir)
    except lib50.Error:
        raise Error(_("Invalid slug for check50. Did you mean something else?"))

    # Load config
    with open(config_file) as f:
        try:
            config = CONFIG_LOADER.load(f.read())
        except lib50.InvalidConfigError:
            raise Error(_("Invalid slug for check50. Did you mean something else?"))

    # Update the config with defaults
    if isinstance(config, dict):
        options.update(config)

    # Apply translations
    if options["translations"]:
        if isinstance(options["translations"], dict):
            translation_options.update(options["translations"])
        options["translations"] = translation_options

    return options


def compile_checks(checks, prompt=False, out_file="__init__.py"):
    """
    Compile YAML checks to a Python file

    :param checks: YAML checks read from config
    :type checkcs: dict
    :param prompt: prompt user if ``out_file`` already exists
    :type prompt: bool
    :param out_file: file to write compiled checks
    :type out_file: str
    :returns: ``out_file``
    :rtype: str
    """

    file_path = check_dir / out_file
    # Prompt to replace __init__.py (compile destination)
    if prompt and file_path.exists():
        if not _yes_no_prompt("check50 will compile the YAML checks to __init__.py, are you sure you want to overwrite its contents?"):
            raise Error("Aborting: could not overwrite to __init__.py")

    # Compile simple checks
    with open(check_dir / out_file, "w") as f:
        f.write(_simple.compile(checks))

    return out_file


def import_file(name, path):
    """
    Import a file given a raw file path.

    :param name: Name of module to be imported
    :type name: str
    :param path: Path to Python file
    :type path: str / Path
    """
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _yes_no_prompt(prompt):
    """
    Raise a prompt, returns True if yes is entered, False if no is entered.
    Will reraise prompt in case of any other reply.
    """
    return _("yes").startswith(input(_("{} [Y/n] ").format(prompt)).lower())
