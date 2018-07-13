import os
import tempfile
from pathlib import Path
import xml.etree.cElementTree as ET

from .api import run, log, Failure
from . import internal

CC = "clang"
CFLAGS = {"std": "c11", "ggdb": True, "lm": True}


def compile(*files, exe_name=None, cc=CC, **cflags):
    """
    Compile files to exe_name (files[0] minus .c by default)
    Uses compiler: {CC} with compilers_flags: {CFLAGS} by default
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

    run(f"{cc} {files}{out_flag}{flags}").exit(0)


def valgrind(command):
    """Run command with valgrind, checks for valgrind errors at the end of the check."""
    xml_file = tempfile.NamedTemporaryFile()
    internal.register.after_check(lambda: _check_valgrind(xml_file))

    # Ideally we'd like for this whole command not to be logged.
    return run(f"valgrind --show-leak-kinds=all --xml=yes --xml-file={xml_file.name} -- {command}")


def _check_valgrind(xml_file):
<<<<<<< HEAD
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
