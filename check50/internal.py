"""
Additional check50 internals exposed to extension writers in addition to the standard API
"""

from pathlib import Path
import atexit
import hashlib
import importlib
import os
import shutil
import tempfile

import lib50

from . import _simple, _exceptions, assertions

#: Directory containing the check and its associated files
check_dir = None

#: Temporary directory in which the current check is being run
run_dir = None

#: Temporary directory that is the root (parent) of all run_dir(s)
run_root_dir = None

#: Directory check50 was run from
student_dir = None

#: Boolean that indicates if a check is currently running
check_running = False

#: The user specified slug used to indentifies the set of checks
slug = None

#: Whether to rewrite ``assert`` statements in checks files to ``check50_assert``.
#: ``None`` means "decide per file" via the ``# ENABLE_CHECK50_ASSERT = 1`` comment flag,
#: ``True``/``False`` force rewriting on/off for every checks file (set by ``--assertion-rewrite``).
assertion_rewrite = None

#: Temporary directory holding the rewritten copies of checks files for this run.
#: Created on first use and removed when check50 exits.
rewrite_dir = None

#: ``lib50`` config loader
CONFIG_LOADER = lib50.config.Loader("check50")
CONFIG_LOADER.scope("files", "include", "exclude", "require")


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
            raise _exceptions.Error("cannot register callback to run after check when no check is running")
        self._after_checks.append(func)

    def after_every(self, func):
        """Run func at the end of every check.

        :param func: callback to be run after every check
        :raises check50.internal.Error: if called when a check is being run"""
        if check_running:
            raise _exceptions.Error("cannot register callback to run after every check when check is running")
        self._after_everies.append(func)

    def before_every(self, func):
        """Run func at the start of every check.

        :param func: callback to be run before every check
        :raises check50.internal.Error: if called when a check is being run"""

        if check_running:
            raise _exceptions.Error("cannot register callback to run before every check when check is running")
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
        raise _exceptions.Error(_("Invalid slug for check50. Did you mean something else?"))

    # Load config
    with open(config_file) as f:
        try:
            config = CONFIG_LOADER.load(f.read())
        except lib50.InvalidConfigError:
            raise _exceptions.Error(_("Invalid slug for check50. Did you mean something else?"))

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
            raise _exceptions.Error("Aborting: could not overwrite to __init__.py")

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


def prepare_checks_file(path):
    """
    Return the path of the checks file that should actually be imported.

    If assertion rewriting applies to ``path`` (see :data:`check50.internal.assertion_rewrite`),
    a copy of the file with every ``assert`` rewritten to ``check50_assert`` is placed in
    :data:`check50.internal.rewrite_dir` and the copy's path is returned; ``path`` is left untouched.
    Otherwise ``path`` is returned as is.

    Each checks file is rewritten at most once per run: worker processes, which re-import the
    checks module, find and reuse the copy made by the parent.

    :param path: Path to the checks file
    :type path: str / Path
    :rtype: Path
    """
    global rewrite_dir

    path = Path(path).resolve()

    if assertion_rewrite is None:
        enabled = assertions.rewrite_enabled(str(path))
    else:
        enabled = assertion_rewrite

    if not enabled:
        return path

    if rewrite_dir is None:
        rewrite_dir = Path(tempfile.mkdtemp(prefix="check50_rewrite_"))
        atexit.register(shutil.rmtree, rewrite_dir, ignore_errors=True)

    # One deterministic name per source file, so re-imports reuse the same copy.
    # Keep the directory and file name for readable tracebacks; the hash disambiguates.
    digest = hashlib.sha1(str(path).encode()).hexdigest()[:8]
    rewritten = rewrite_dir / f"{path.parent.name}-{path.stem}-{digest}.py"

    if not rewritten.exists():
        # Build the copy under a unique name, then move it into place atomically so that a
        # concurrent worker never imports a half-written file
        with tempfile.NamedTemporaryFile(dir=rewrite_dir, suffix=".partial", delete=False) as tmp:
            partial = Path(tmp.name)
        try:
            shutil.copyfile(path, partial)
            # Report syntax errors against the original checks file, not the staging copy
            assertions.rewrite(str(partial), filename=str(path))
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        os.replace(partial, rewritten)

    return rewritten


def _yes_no_prompt(prompt):
    """
    Raise a prompt, returns True if yes is entered, False if no is entered.
    Will reraise prompt in case of any other reply.
    """
    return _("yes").startswith(input(_("{} [Y/n] ").format(prompt)).lower())
