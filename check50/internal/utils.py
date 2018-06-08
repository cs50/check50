import os
import shutil
from pexpect.exceptions import EOF

def copy(src, dst):
    """Copy src to dst, copying recursively if src is a directory"""
    try:
        shutil.copy(src, dst)
    except IsADirectoryError:
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.copytree(src, dst)


def raw(s):
    """Get raw representation of s, truncating if too long"""

    if isinstance(s, list):
        s = "\n".join(s)

    if s == EOF:
        return "EOF"

    s = repr(s)  # get raw representation of string
    s = s[1:-1]  # strip away quotation marks
    if len(s) > 15:
        s = s[:15] + "..."  # truncate if too long
    return "\"{}\"".format(s)
