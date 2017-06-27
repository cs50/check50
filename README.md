# check50

## Running `check50`

Run `check50` via:

```
python check50.py identifier [files to check]
```

For example, to check `greedy`, assuming you have a file called `greedy.c` in the same directory as `check50.py`, run:

```
python check50.py 2017/x/greedy greedy.c
```

Identifier names are given by the filenames in the `checks` directory, with subdirectories specified by the `/` symbol.
To check multiple files, separate each filename with a space. Alternatively, not specifying any files will by default use all files
in the current directory (TODO: change this to use the `exclude` files).

## Contributing to `check50`

To contribute to `check50`:

* Fork the `cs50/check50` repository (button in the upper-right corner of the window)
* Clone the forked repository, committing and pushing new changes.
* Submit a pull request to `cs50/check50` from the forked repository.

### Check File Structure

All checks are located in a subdirectory of the `checks` directory.
Each problem which requires checks has its own `checks.py` file.
`checks.py` should contain a single class, named after the problem, which is a sublcass of `check50.TestCase`.
Individual checks are methods defined within the class. 
Check functions must be decorated with the `@check` decorator, and must have a one-line docstring which
describes what the method is checking. The `@check` decorator may optionally take a single parameter:
the name of another check method which must have passed before the decorated check can run. Before a
check runs, all files from the dependency check's working directory are copied into the decorated check's
working directory.

### Check Successes and Failures

To indicate that a check has failed, the exception `check50.Error` must be raised.
This can be raised directly by the check method, or indirectly via a method of `check50.TestCase`
which is called by the check method.

`check50.Error` takes a single parameter. If the parameter is a string, it represents the 
reason for the check failure. If the parameter is a tuple of `(observed, desired)`, then it
represents that `observed` was the observed output, whereas `desired` was the desired output.

If a check method finishes without raising `check50.Error`, then the test is assumed to have passed.

### `rationale`, `helpers`, and `log`

In addition to keeping track of the success and failure of tests,
`check50` maintains three other per-test-case values that store information
about what took place during a given check.

`self.rationale` is a string, representing the reason that the check failed, and is set by `check50.Error`.

`self.helpers` is a list of strings, representing zero or more lines of suggestions as to why a check
may have failed. Check functions may optionally choose to add to `self.helpers` if they can guess why
a particular `check50.Error` was raised.

`self.log` is a list of strings, representing what steps took place during the check function.
Check functions may optionally add to `self.log`, and methods in `check50.TestCase` will also
add to `self.log`.

### Sample Check and Explanation

```
@check("compiles")
def test5(self):
    """5 minutes equals 60 bottles."""
    self.spawn("./water").stdin("5").stdout("^.*60.*$", 60).exit(0)
```

The `@check` decorator indicates that this is a check method. The parameter `"compiles"`
means that unless the `compiles` check passed, this check (`test5`) will not run. It also 
means that before this test is run, the state of the working directory after the `"compiles"`
check ran will be copied into `test5`'s working directory (including the compiled `water` 
binary).

The docstring `"5 minutes equal 60 bottles."` is a description of what this check
method is testing.

First, `self.spawn("./water")` is called, which executes `./water` as a child process.
Then, the string `"5"` is passed into the program via the `.stdin()` method.

The `.stdout()` method takes two parameters: the first is a regular expression indicating
the desired output of the program. The second parameter is a human-friendly representation
of the desired output, which will be displayed to students if the check fails. Here,
we assert that the output of `./water` should match the regular expression `"^.*60.*$"`.
If this is not the case, a `check50.Error` will be raised.

Finally, we assert that the exit status of the program is `0`.

### `check50.TestCase` 

#### `checkfile(self, filename)`

Takes a relative path to a file located in the directory containing `check.py`
and returns its contents as a string.

#### `diff(self, f1, f2)`

Takes two files, `f1` and `f2`, which can be strings or `check50.File` types.
If the filemaes are strings, they are interpreted as relative paths in the 
temporary check directory. If the filenames are of type `check50.File`,
then type are considered relative paths in the directory containing
`check.py`.

Compares the two files, and outputs `0` if the two files are the same,
and nonzero otherwise.

#### `exists(self, filename)`

Asserts that `filename` exists, and raises a `check50.Error` otherwise.

#### `hash(self, filename)`

Hashes `filename` using SHA-256, and returns the hash of the file.

#### `spawn(self, cmd, env)`

Spawns the child process running `cmd` with the environment `env`.
Returns a `check50.Child`, which is a wrapper on a `pexpect` child process.

#### `include(self, path)`

Includes `path`, a relative path in the directory containing `check.py`
into the temporary check directory.

#### `append_code(self, filename, codefile)`

Appends the contents of `codefile` to the end of `filename` in the
temporary directory. Useful for replacing a Python function during
testing.

#### `fail(self, rationale)`

Fails the test with the given `rationale`.

### `check50.Child`

#### `stdin(self, line, prompt=True)`

Passes `line` as input to the child process.
The `prompt` variable, default `True`, determines whether 
`check50` should wait for a nonzero-character prompt to appear 
before passing in `line`.

#### `stdout(self, output=None, str_output=None)`

Asserts that, at program's termination, the
child process produces output that matches the regex `output`,
and raises a `check50.Error` otherwise. If the error is raised,
the `rationale` includes that the expected output was `str_output`.

If `output` is `None` (i.e. by default, if no parameters are passed 
into the `stdout` function), then the function returns a string
representing the program's output.

#### `reject(self)`

Asserts that the child process should have rejected an input
and prompted for another input. Typically called after a call to `.stdin()`.
If the child process did not prompt for another input, then a 
`check50.Error` will be raised.

#### `exit(self, code=None)`

If `code` is not `None`, then `exit` asserts that the program terminated
with exit code `code`, and raises a `check50.Error` otherwise.

If `code` is `None`, then `exit` returns the exit code of the program.

#### `kill(self)`

Terminates the child process.
