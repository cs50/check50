"""
Additional check50 internals exposed to extension writers in addition to the standard API
"""
import yaml
import re
from collections import OrderedDict
from contextlib import contextmanager

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
        """run func once at the end of the check, then discard func"""
        self._after_checks.append(func)

    def after_every(self, func):
        """run func at the end of every check"""
        self._after_everies.append(func)

    def before_every(self, func):
        """run func at the start of every check"""
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

_data = {}
register.before_every(_data.clear)

def data(**kwargs):
    """adds any key-value pairs to the data object of the json payload of a check"""
    _data.update(kwargs)


def _run(arg):
    return f'.run("{arg}")'

def _stdin(arg):
    if isinstance(arg, list):
        arg = "\\n".join(arg)
    return f'.stdin("{arg}", prompt=False)'

def _stdout(arg):
    if isinstance(arg, list):
        arg = "\\n".join(arg)
    return f'.stdout("{re.escape(arg)}")'

def _exit(arg):
    try:
        arg = int(arg)
    except ValueError:
        raise InvalidArgument(f"exit command only accepts integers, not {arg}")
    return f'.exit({arg})'

COMMANDS = OrderedDict([("run", _run), ("stdin", _stdin), ("stdout", _stdout), ("exit", _exit)])

def compile(path):
    """returns compiled check50 checks from config file checks in path"""
    with open(path) as f:
        try:
            content = yaml.load(f)
        except yaml.scanner.ScannerError as e:
            raise CompileError(str(e))

    out = "import check50\n"

    for check_name in content:
        out += "\n" + _compile_check(check_name, content[check_name])

    return out

def _compile_check(name, content):
    indent = "    "
    out = f'@check50.check()\ndef {name}():\n{indent}"""{name}"""'

    for run in content:
        _validate(name, run)
        _preprocess(run)

        out += f"\n{indent}check50"

        for command_name in COMMANDS:
            if command_name in run:
                out += COMMANDS[command_name](run[command_name])

    return f"{out}\n"

def _validate(name, run):
    for key in run:
        if key not in COMMANDS:
            raise UnsupportedCommand(f"{key} is not a valid command in check {name}, use only: {COMMANDS.keys()}")

    for required_command in ["run"]:
        if required_command not in run:
            raise MissingCommand(f"Missing {required_command} in check {name}")

def _preprocess(run):
    if "exit" not in run:
        run["exit"] = 0

class CompileError(Exception):
    pass

class UnsupportedCommand(CompileError):
    pass

class MissingCommand(CompileError):
    pass

class InvalidArgument(CompileError):
    pass
