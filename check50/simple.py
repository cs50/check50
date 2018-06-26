"""
Functions that compile "simple" YAML checks into our standard python checks
"""

import re


def compile(checks):
    """returns compiled check50 checks from simple YAML checks in path"""

    out = ["import check50"]

    for name, check in checks.items():
        out.append(_compile_check(name, check))

    return "\n\n".join(out)


def _run(arg):
    return f'.run("{arg}")'


def _stdin(arg):
    if isinstance(arg, list):
        arg = r"\n".join(arg)

    arg = arg.replace("\n", r"\n").replace("\t", r"\t").replace('"', '\"')
    return f'.stdin("{arg}")'


def _stdout(arg):
    if isinstance(arg, list):
        arg = r"\n".join(arg)
    arg = arg.replace("\n", r"\n").replace("\t", r"\t").replace('"', '\"')
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

    check_name = name.replace(' ', '_').replace('-', '_')
    if check_name[0].isdigit():
        check_name = f"_{check_name}"


    if not re.match("\w+", check_name):
        raise CompileError(f"{name} is not a valid name for a check, " \
            "check names should consist only of alphanumeric characters, underscores, and spaces")

    out = ["@check()",
           f"def {check_name}():",
           f'{indent}"""{name}"""']

    for run in check:
        _validate(name, run)
        _preprocess(run)

        line = [f"{indent}check50"]

        for command_name in COMMANDS:
            if command_name in run:
                line.append(COMMANDS[command_name](run[command_name]))
        out.append("".join(line))

    return "\n".join(out)


def _validate(name, run):
    for key in run:
        if key not in COMMANDS:
            raise UnsupportedCommand(
                f"{key} is not a valid command in check {name}, use only: {COMMANDS.keys()}")

    for required_command in ["run"]:
        if required_command not in run:
            raise MissingCommand(f"Missing {required_command} in check {name}")


def _preprocess(run):
    if "exit" not in run:
        run["exit"] = None


class CompileError(Exception):
    pass


class UnsupportedCommand(CompileError):
    pass


class MissingCommand(CompileError):
    pass


class InvalidArgument(CompileError):
    pass
