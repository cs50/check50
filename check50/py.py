import importlib
from pathlib import Path

from . import internal
from .api import Failure, exists, log


def append_code(original, codefile):
    """Append codefile to original."""
    with open(codefile) as code, open(original, "a") as o:
        o.write("\n")
        o.writelines(code)


def import_(path):
    """Given a raw file path, import a module."""
    exists(path)
    log(_("importing {}...").format(path))
    name = Path(path).stem
    try:
        return internal.import_file(name, path)
    except Exception as e:
        raise Failure(str(e))
