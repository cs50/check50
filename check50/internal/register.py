_befores = []
_afters = []

def register_before(func):
    _befores.append(func)

def register_after(func):
    _afters.append(func)

def before():
    for func in _befores:
        func()

def after():
    for func in _afters:
        func()
