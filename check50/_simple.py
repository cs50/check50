"""
Functions that compile "simple" YAML checks into our standard python checks
"""

import re


def compile(checks):
    """Returns compiled check50 checks from simple YAML checks in path."""

    out = ["import check50"]

    for name, check in checks.items():
        out.append(_compile_check(name, check))

    return "\n\n".join(out)


def _run(arg):
    return f'.run("{arg}")'


def _stdin(arg):
    if isinstance(arg, list):
        arg = r"\n".join(str(a) for a in arg)

    arg = str(arg).replace("\n", r"\n").replace("\t", r"\t").replace('"', '\"')
    return f'.stdin("{arg}", prompt=False)'


def _stdout(arg):
    if isinstance(arg, list):
        arg = r"\n".join(str(a) for a in arg)
    arg = str(arg).replace("\n", r"\n").replace("\t", r"\t").replace('"', '\"')
    return f'.stdout("{arg}", regex=False)'


def _exit(arg):
    if arg is None:
        return ".exit()"

    try:
        arg = int(arg)
    except ValueError:
        raise InvalidArgument(f"exit command only accepts integers, not {arg}")
    return f'.exit({arg})'


COMMANDS = {"run": _run, "stdin": _stdin, "stdout": _stdout, "exit": _exit}


def _compile_check(name, check):
    indent = " " * 4

    # Allow check names to contain spaces/dashes, but replace them with underscores
    check_name = name.replace(' ', '_').replace('-', '_')

    # Allow check names to start with numbers by prepending an _ to them
    if check_name[0].isdigit():
        check_name = f"_{check_name}"

    if not re.match("\w+", check_name):
        raise CompileError(
                _("{} is not a valid name for a check; check names should consist only of alphanumeric characters, underscores, and spaces").format(name))

    out = ["@check50.check()",
           f"def {check_name}():",
           f'{indent}"""{name}"""']

    for run in check:
        _validate(name, run)

        # Append exit with no args if unspecified
        if "exit" not in run:
            run["exit"] = None

        line = [f"{indent}check50"]

        for command_name in COMMANDS:
            if command_name in run:
                line.append(COMMANDS[command_name](run[command_name]))
        out.append("".join(line))

    return "\n".join(out)


def _validate(name, run):
    if run == "run":
        raise CompileError(_("You forgot a - in front of run"))

    for key in run:
        if key not in COMMANDS:
            raise UnsupportedCommand(
                _("{} is not a valid command in check {}, use only: {}").format(key, name, COMMANDS))

    for required_command in ["run"]:
        if required_command not in run:
            raise MissingCommand(_("Missing {} in check {}").format(required_name, name))


class CompileError(Exception):
    pass


class UnsupportedCommand(CompileError):
    pass


class MissingCommand(CompileError):
    pass


class InvalidArgument(CompileError):
    pass
