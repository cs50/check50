import importlib
from pathlib import Path
import py_compile

from . import internal
from ._api import Failure, exists, log


def append_code(original, codefile):
    """Append the contents of one file to another.

    :param original: name of file that will be appended to
    :type original: str
    :param codefile: name of file that will be appende
    :type codefile: str

    This function is particularly useful when one wants to replace a function
    in student code with their own implementation of one. If two functions are
    defined with the same name in Python, the latter definition is taken so overwriting
    a function is as simple as writing it to a file and then appending it to the
    student's code.

    Example usage::

        # Include a file containing our own implementation of a lookup function.
        check50.include("lookup.py")

        # Overwrite the lookup function in helpers.py with our own implementation.
        check50.py.append_code("helpers.py", "lookup.py")
    """
    with open(codefile) as code, open(original, "a") as o:
        o.write("\n")
        o.writelines(code)


def import_(path):
    """Import a Python program given a raw file path

    :param path: path to python file to be imported
    :type path: str
    :raises check50.Failure: if ``path`` doesn't exist, or if the Python file at ``path`` throws an exception when imported.
    """
    exists(path)
    log(_("importing {}...").format(path))
    name = Path(path).stem
    try:
        return internal.import_file(name, path)
    except Exception as e:
        raise Failure(str(e))

def compile(file):
    """
    Compile a Python program into byte code

    :param file: file to be compiled
    :raises check50.Failure: if compilation fails e.g. if there is a SyntaxError
    """
    log(_("compiling {} into byte code...").format(file))

    try:
        py_compile.compile(file, doraise=True)
    except py_compile.PyCompileError as e:
        log(_("Exception raised: "))
        for line in e.msg.splitlines():
            log(line)

        raise Failure(_("{} raised while compiling {} (see the log for more details)").format(e.exc_type_name, file))
