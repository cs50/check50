import pathlib
import check50
import check50.internal as internal

@check50.check()
def foo():
    """directories exist"""
    assert internal.run_dir.resolve() == pathlib.Path.cwd()
    assert internal.run_dir.parent == internal.run_root_dir

assert internal.run_root_dir.exists()
assert internal.run_root_dir.resolve() == pathlib.Path.cwd()

assert internal.student_dir.exists()
with open(internal.student_dir / "foo.py") as f:
    student_dir = pathlib.Path(f.read().strip())
assert internal.student_dir == student_dir

assert internal.check_dir.exists()
assert internal.check_dir.name == "internal_directories"
