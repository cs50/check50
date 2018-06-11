import os
import tempfile
import xml.etree.cElementTree as ET

from .api import run, log, Failure
from . import internal

CC = "clang"
CFLAGS = "-std=c11 -O0 -ggdb3" # etc.


def compile(file_name, exe_name=None):
    if exe_name is None and file_name.endswith(".c"):
        exe_name = file_name.split(".c")[0]

    out_flag = f"-o {exe_name}" if exe_name is not None else ""

    run(f"{CC} {file_name} {out_flag} {CFLAGS}").exit(0)


def valgrind(command):
    xml_file = tempfile.NamedTemporaryFile()
    register.after(lambda: _check_valgrind(xml_file))

    # ideally we'd like for this whole command not to be logged.
    return run(f"valgrind --show-leak-kinds=all --xml=yes --xml-file={xml_file.name} -- {command}")


def _check_valgrind(xml_file):
    """Log and report any errors encountered by valgrind"""
    log("checking for valgrind errors... ")

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
            if obj is not None and os.path.dirname(obj.text) == run_dir:
                location = frame.find("file"), frame.find("line")
                if None not in location:
                    msg.append(
                        ": (file: {}, line: {})".format(
                            location[0].text, location[1].text))
                break

        msg = "".join(msg)
        if msg not in reported:
            log(msg)
            reported.add(msg)

    # Only raise exception if we encountered errors.
    if reported:
        raise Failure("valgrind tests failed; rerun with --log for more information.")
