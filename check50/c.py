import os
import re
import tempfile
from pathlib import Path
import xml.etree.cElementTree as ET

from ._api import run, log, Failure
from . import internal

#: Default compiler for :func:`check50.c.compile`
CC = "clang"

#: Default CFLAGS for :func:`check50.c.compile`
CFLAGS = {"std": "c11", "ggdb": True, "lm": True}


def compile(*files, exe_name=None, cc=CC, **cflags):
    """
    Compile C source files.

    :param files: filenames to be compiled
    :param exe_name: name of resulting executable
    :param cc: compiler to use (:data:`check50.c.CC` by default)
    :param cflags: additional flags to pass to the compiler
    :raises check50.Failure: if compilation failed (i.e., if the compiler returns a non-zero exit status).
    :raises RuntimeError: if no filenames are specified

    If ``exe_name`` is None, :func:`check50.c.compile` will default to the first
    file specified sans the ``.c`` extension::


        check50.c.compile("foo.c", "bar.c") # clang foo.c bar.c -o foo -std=c11 -ggdb -lm

    Additional CFLAGS may be passed as keyword arguments like so::

        check50.c.compile("foo.c", "bar.c", lcs50=True) # clang foo.c bar.c -o foo -std=c11 -ggdb -lm -lcs50

    In the same vein, the default CFLAGS may be overriden via keyword arguments::

        check50.c.compile("foo.c", "bar.c", std="c99", lm=False) # clang foo.c bar.c -o foo -std=c99 -ggdb
    """

    if not files:
        raise RuntimeError(_("compile requires at least one file"))

    if exe_name is None and files[0].endswith(".c"):
        exe_name = Path(files[0]).stem

    files = " ".join(files)

    flags = CFLAGS.copy()
    flags.update(cflags)
    flags = " ".join((f"-{flag}" + (f"={value}" if value is not True else "")).replace("_", "-")
                     for flag, value in flags.items() if value)

    out_flag = f" -o {exe_name} " if exe_name is not None else " "

    process = run(f"{cc} {files}{out_flag}{flags}")

    # Strip out ANSI codes
    stdout = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "",  process.stdout())

    if process.exitcode != 0:
        for line in stdout.splitlines():
            log(line)
        raise Failure("code failed to compile")


def valgrind(command, env={}):
    """Run a command with valgrind.

    :param command: command to be run
    :type command: str
    :param env: environment in which to run command
    :type env: str
    :raises check50.Failure: if, at the end of the check, valgrind reports any errors

    This function works exactly like :func:`check50.run`, with the additional effect that ``command`` is run through
    ``valgrind`` and ``valgrind``'s output is automatically reviewed at the end of the check for memory leaks and other
    bugs. If ``valgrind`` reports any issues, the check is failed and student-friendly messages are printed to the log.

    Example usage::

        check50.c.valgrind("./leaky").stdin("foo").stdout("bar").exit(0)

    .. note::
        It is recommended that the student's code is compiled with the `-ggdb`
        flag so that additional information, such as the file and line number at which
        the issue was detected can be included in the log as well.
    """
    xml_file = tempfile.NamedTemporaryFile()
    internal.register.after_check(lambda: _check_valgrind(xml_file))

    # Ideally we'd like for this whole command not to be logged.
    return run(f"valgrind --show-leak-kinds=all --xml=yes --xml-file={xml_file.name} -- {command}", env=env)


def _check_valgrind(xml_file):
    """Log and report any errors encountered by valgrind."""
    log(_("checking for valgrind errors..."))

    # Load XML file created by valgrind
    xml = ET.ElementTree(file=xml_file)

    # Ensure that we don't get duplicate error messages.
    reported = set()
    for error in xml.iterfind("error"):
        # Type of error valgrind encountered
        kind = error.find("kind").text

        # Valgrind's error message
        what = error.find("xwhat/text" if kind.startswith("Leak_") else "what").text

        # Error message that we will report
        msg = ["\t", what]

        # Find first stack frame within student's code.
        for frame in error.iterfind("stack/frame"):
            obj = frame.find("obj")
            if obj is not None and internal.run_dir in Path(obj.text).parents:
                file, line = frame.find("file"), frame.find("line")
                if file is not None and line is not None:
                    msg.append(f": ({_('file')}: {file.text}, {_('line')}: {line.text})")
                break

        msg = "".join(msg)
        if msg not in reported:
            log(msg)
            reported.add(msg)

    # Only raise exception if we encountered errors.
    if reported:
        raise Failure(_("valgrind tests failed; rerun with --log for more information."))
