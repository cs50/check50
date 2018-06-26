# check50 [![Build Status](https://www.travis-ci.org/cs50/check50.svg?branch=check50api-pool)](https://www.travis-ci.org/cs50/check50)

Check50 is a testing tool for checking student code. As a student you can use check50 to check your CS50 problem sets or any other Problem sets for which check50 checks exist. Check50 allows teachers to automatically grade code on correctness and to provide automatic feedback while students are coding.

## Checks
In Check50 the actual checks are decoupled from the tool. You can find CS50's set of checks for CS50 problem sets at [/cs50/checks](https://github.com/cs50/checks). If you would like to develop your own set of checks such that you can use check50 in your own course [jump to writing checks](## Writing checks).

Under the hood, checks are naked Python functions decorated with the ``` @check50.check``` decorator. Check50 exposes several functions, [documented below](## Docs), that allow you to easily write checks for input/output testing. Check50 comes with two builtin extensions: `c` and `flask`. These extensions add extra functionality for C and Python's Flask framework to check50's core.

By design check50 is extensible. If you want to add support for other programming languages / frameworks and you are comfortable with Python please [check out writing extensions](## Writing extensions).

## Docs

`check50.check`

`check50.exists`

`check50.run`

`check50.Process.stdin`

`check50.Process.stdout`

`check50.Process.exit`

`check50.Process.reject`

`check50.Process.kill`

`check50.Failure`

`check50.Mismatch`

`check50.diff`

`check50.hash`

`check50.log`

`check50.include`

`check50.import_checks`

## Writing checks

### Simple (YAML) checks

## Writing extensions

### check50.internal
