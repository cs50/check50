from enum import Enum
from functools import wraps
from time import sleep


checks = []
results = {}


def check(*args):
    def decorator(f):
        checks.append(f.__name__)
        @wraps(f)
        def wrapper(self):
            for arg in args:
                if not results.get(arg):
                    print(f"Skipping {f.__name__} because {depend} not called yet") # TODO: try again later
                    results[f.__name__] = Result.SKIP
                    return
                elif results.get(arg) == Result.SKIP:
                    print(f"Skipping {f.__name__} because {depend} skipped")
                    results[f.__name__] = Result.SKIP
                    return
                elif results.get(arg) == Result.FAIL:
                    print(f"Skipping {f.__name__} because {depend} failed")
                    results[f.__name__] = Result.SKIP
                    return
            print(f"Calling {f.__name__}")
            try:
                f()
            except:
                results[f.__name__] = Result.FAIL
            results[f.__name__] = Result.PASS
        return wrapper
    return decorator


class Result(Enum):
    PASS = 1
    FAIL = 2
    SKIP = 3


class Checks:

    def __init__(self):
        for check in checks:
            getattr(self, check)()

    @check()
    def exists():
        sleep(1)

    @check("exists")
    def compiles():
        sleep(3)

    @check("compiles")
    def foo():
        sleep(2)

    @check("compiles")
    def bar():
        sleep(1)

    @check("compiles")
    def baz():
        sleep(0)

    @check("exists")
    def qux():
        raise RuntimeError()

    @check()
    def quux():
        sleep(0)

if __name__ == "__main__":
    c = Checks()
    for check in results:
        print(f"{check}: {results[check]}")
