import os
import tempfile
import xml.etree.cElementTree as ET

import check50
from check50.internal import register, globals


def valgrind(command):
    xml_file = tempfile.NamedTemporaryFile()

    def check():
        try:
            _check_valgrind(xml_file)
        finally:
            xml_file.close()

    register.register_after(check)
    # ideally we'd like for this whole command not to be logged.
    return check50.run(f"valgrind --show-leak-kinds=all --xml=yes --xml-file={xml_file.name} -- {command}")


def _check_valgrind(xml_file):
    """Log and report any errors encountered by valgrind"""
    check50.log("checking for valgrind errors... ")

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
            if obj is not None and os.path.dirname(obj.text) == globals.cwd:
                location = frame.find("file"), frame.find("line")
                if None not in location:
                    msg.append(
                        ": (file: {}, line: {})".format(
                            location[0].text, location[1].text))
                break

        msg = "".join(msg)
        if msg not in reported:
            check50.log(msg)
            reported.add(msg)

    # Only raise exception if we encountered errors.
    if reported:
        raise check50.Error("valgrind tests failed; rerun with --log for more information.")
