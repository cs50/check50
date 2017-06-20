# check50

## Running `check50`

Run `check50` via:

```
python check50.py identifier [files to check]
```

For example, to check `greedy`, assuming you have a file called `greedy.c` in the same directory as `check50.py`, run:

```
python check50.py greedy greedy.c
```

Identifier names are given by the filenames in the `checks` directory, with subdirectories specified by the `.` symbol (e.g. `mario.less` or `mario.more`).
To check multiple files, separate each filename with a space. Alternatively, not specifying any files will by default use all files
in the current directory (TODO: change this to use the `exclude` files).

## Contributing to `check50`

To contribute to `check50`:

* Fork the `cs50/check50` repository (button in the upper-right corner of the window)
* Clone the forked repository, committing and pushing new changes.
* Submit a pull request to `cs50/check50` from the forked repository.

### Checks

All checks are located in the `checks` directory or one of its subdirectories.
Each problem which requires checks has its own `.py` file named for the problem.

