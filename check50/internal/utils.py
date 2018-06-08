import os
import shutil

def copy(src, dst):
    """Copy src to dst, copying recursively if src is a directory"""
    try:
        shutil.copy(src, dst)
    except IsADirectoryError:
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.copytree(src, dst)

