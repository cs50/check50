"""
Additional check50 internals exposed to extension writers in addition to the standard API
"""

import importlib
from pathlib import Path
import sys

import yaml

from . import simple

# Directory containing the check and its associated files
check_dir = None

# Temporary directory in which check is being run
run_dir = None


class Register:
    def __init__(self):
        self._before_everies = []
        self._after_everies = []
        self._after_checks = []

    def after_check(self, func):
        """Run func once at the end of the check, then discard func."""
        self._after_checks.append(func)

    def after_every(self, func):
        """Run func at the end of every check."""
        self._after_everies.append(func)

    def before_every(self, func):
        """Run func at the start of every check."""
        self._before_everies.append(func)

    def __enter__(self):
        for f in self._before_everies:
            f()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Only run 'afters' when check has passed
        if exc_type is not None:
            return

        while self._after_checks:
            self._after_checks.pop()()

        for f in self._after_everies:
            f()


register = Register()


def load_config(check_dir):
    options = {
        "checks": "__init__.py",
        "dependencies": None,
        "translations": None
    }

    translation_options = {
        "localedir": "locale",
        "domain": "messages",
        "native": "en"
    }

    config_file = check_dir / ".cs50.yaml"

    with open(config_file) as f:
        config = yaml.safe_load(f)["check50"]

    if isinstance(config, dict):
        options.update(config)

    if options["translations"]:
        if isinstance(options["translations"], dict):
            translation_options.update(options["translations"])
        options["translations"] = translation_options


    if isinstance(options["checks"], dict):
        with open(check_dir / "__init__.py", "w") as f:
            f.write(simple.compile(options["checks"]))
        options["checks"] = "__init__.py"

    return options


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
