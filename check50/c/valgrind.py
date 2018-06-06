import os
import xml.etree.cElementTree as ET

import check50
import check50.internal


_valgrind_log = ".valgrind.xml"

def valgrind(command):
    check50.internal.register_after(lambda : _check_valgrind())
    return check50.run(f"valgrind {command}")


def _check_valgrind():
    """Log and report any errors encountered by valgrind"""
    check50.log("checking for valgrind errors... ")

    # Load XML file created by valgrind
    xml = ET.ElementTree(file=os.path.join(check50.test_dir(), _valgrind_log))

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
            if obj is not None and os.path.dirname(obj.text) == check50.internal.check_dir:
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
