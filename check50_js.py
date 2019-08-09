import contextlib
import io

import check50
from bond import make_bond


@contextlib.contextmanager
def capture_stdout():
	"""Redirect stdout."""
	f = io.StringIO()
	with contextlib.redirect_stdout(f):
		yield f


def interface(file=None):
	"""
	Interface with a JavaScript interpreter (node).
	If file is passed, evaluate the contents of file within the interpreter.
	"""
	inter = make_bond("javascript")

	if file:
	    with open(file) as f:
	        content = f.read()
	    inter.eval_block(content)

	return inter


def function_exists(function_name, interface):
	"""
	Check whether function_name is defined within interface.
	Raises Failure if not.
	"""
	defined = interface.call(f'() => typeof {function_name} === "function"')
	if not defined :
		raise check50.Failure(f"{function_name} is not defined")
