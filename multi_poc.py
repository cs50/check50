'''
Proof of concept for a basic multiprocessing script.
'''
import multiprocessing
import collections

from enum import Enum
from functools import wraps
from time import sleep

class Result(Enum):
    PASS = 1
    FAIL = 2
    SKIP = 3

class OrderedAsyncManager:
    '''
    Holds a map of job-dependency strings to the jobs that depend on the completion of the function mapping
    to that key. e.g., the index of 'compile' contains all of the functions that must wait for the 'compile'
    function to finish running.

    Each index will map to a list of 1 or more function objects to later be called via the dispatch method.
    '''

    class JobBatch:
        """
        Helper class that holds the child processes of the current thread
        """
        def __init__(self):
            self.jobs = []

        def __iter__(self):
            return iter(self.jobs)

        def __getitem__(self, idx):
            return self.jobs[idx]

        def __len__(self):
            return len(self.jobs)

        def start(self, fn):
            self.jobs.append(multiprocessing.Process(target=fn))
            self.jobs[-1].start()

        def wait(self):
            for job in self:
                job.join()

    def __init__(self):
        self.job_map = collections.defaultdict(list)
        self.results = {
            None : Result.PASS
        }

    def dispatch(self, key=None):
        '''
        Given a key, deploy a multiprocessing queue with all of the functions held in the job_map at the
        index of said key.
        '''
        batch = self.JobBatch()
        if self.results[key] == Result.SKIP:
            for f in self.job_map[key]:
                self.results[f.__name__] = Result.SKIP
                print(f'Skipping {f.__name__} because {key} was skipped!')
        elif self.results[key] == Result.FAIL:
            for f in self.job_map[key]:
                self.results[f.__name__] = Result.SKIP
                print(f'Skipping {f.__name__} because {key} failed!')
        else:
            for f in self.job_map[key]:
                batch.start(f)
        return batch

manager = OrderedAsyncManager()

def check(*args):
    def decorator(f):
        @wraps(f)
        def wrapper():
            for arg in args:
                pass
            print(f"Calling {f.__name__}")
            try:
                f()
                manager.results[f.__name__] = Result.PASS
            except:
                manager.results[f.__name__] = Result.FAIL
            # if there is a pool of functions defined by a keyword, dispatch it
            if f.__name__ in manager.job_map:
                manager.dispatch(f.__name__).wait()
        key = args[0] if args else None
        manager.job_map[key].append(wrapper)
        return wrapper
    return decorator

class Checks:
    @check()
    def exists():
        sleep(1)

    @check("exists")
    def compiles():
        sleep(3)

    @check("exists")
    def compiles2():
        sleep(3)

    @check("exists")
    def compiles3():
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
        sleep(2)

if __name__ == '__main__':
    # begin the manager by executing jobs requiring no dependencies
    print("Before")
    manager.dispatch().wait()
    print("After")
