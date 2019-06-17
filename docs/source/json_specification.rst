.. _json_specification:

JSON specification
==========================
Check50 can create a machine readable output in the form of `json`. For instance, running check50 with `-o json` on a non compiling implementation of one of our problems called caesar:

.. code-block:: bash

    check50 cs50/problems/2018/x/caesar -o json

Produces the following:

.. code-block:: json

    {
        "slug": "cs50/problems/2018/x/caesar",
        "results": [
            {
                "name": "exists",
                "description": "caesar.c exists.",
                "passed": true,
                "log": [
                    "checking that caesar.c exists..."
                ],
                "cause": null,
                "data": {},
                "dependency": null
            },
            {
                "name": "compiles",
                "description": "caesar.c compiles.",
                "passed": false,
                "log": [
                    "running clang caesar.c -o caesar -std=c11 -ggdb -lm -lcs50...",
                    "caesar.c:24:5: warning: implicit declaration of function 'f' is invalid in C99",
                    "      [-Wimplicit-function-declaration]",
                    "    f (argc != 2)",
                    "    ^",
                    "caesar.c:24:18: error: expected ';' after expression",
                    "    f (argc != 2)",
                    "                 ^",
                    "                 ;",
                    "1 warning and 1 error generated."
                ],
                "cause": {
                    "rationale": "code failed to compile",
                    "help": null
                },
                "data": {},
                "dependency": "exists"
            },
            {
                "name": "encrypts_a_as_b",
                "description": "encrypts \"a\" as \"b\" using 1 as key",
                "passed": null,
                "log": [],
                "cause": {
                    "rationale": "can't check until a frown turns upside down"
                },
                "data": {},
                "dependency": "compiles"
            },
        ],
        "version": "3.0.0"
    }

Top level
*************************
You will find three keys at the top level of the json output: `slug`, `results` and `version`.

1. **slug** tells you the slug you ran check50 with. In the example above that is `cs50/problems/2018/x/caesar`.
2. **results** is the payload of check50, a list of the results of all checks. More on this key below.
3. **version** is the version of check50 used to run the checks.

In case check50 ran into an error, for instance because of an invalid slug, you will find the following three keys at the top level:

1. **slug** tells you the slug you ran check50 with. Note that this slug could be invalid.
2. **error** is the information on the error check50 ran into. More on this key below.
3. **version** is the version of check50 used to run the checks.

results
*************************
In case check50 ran successfully, that is not to say all checks passed but rather that check50 ran all checks, you will find a `results` key at the top level. This key contains a list of check results. Each result always contains the following keys:

1. **name** is the name of the check.
2. **description** is the description of the check.
3. **passed** is a tertiary value. `true`/`false` signals the check has passed or not respectively. The third possible state, `null`, signals that the check was skipped or an error occurred. You can distinct between the cases of an error or a skipped check by inspecting the `cause` key.
4. **log** is a list of strings, each string is one entry in the log.
5. **cause** is the cause of a failing check. In case a check passed, cause will be `null`. In every other case you will an object here with containing information on why it did not pass. More on this key below.
6. **data** is always an object containing any additional data communicated during the check via the `check50.data` api call. More on this key below.
7. **dependency** is the name of the check on which this check depends. This key allows you to trace the chain of dependencies.

*************************
cause
*************************
The cause key of a result is either `null` in case the check passed or an object containing information on why the check did not pass. This key is by design an open-ended object. Everything in the `.payload` attribute of a `check50.Failure` will be put in the `cause` key. Through this mechanism you can communicate any information you want from a failing check to the results. Depending on what occurred check50 adds the following keys to `cause`:

1. **rationale** is an explanation of what went wrong and is always a part of `cause`. Could be that the code you are checking exited with a non-zero exitcode or output you were expecting was not printed.
2. **help** is an additional help message that can be supplied alongside rationale.
3. **expected** and **actual** are keys that always appear in a pair. In case you are expecting X as output, but Y was found instead, you will find these keys containing X and Y in the `cause` field. If you raise a `check50.Mismatch` from within a check, these are the keys you will find in the output.
4. **error** appears in `cause` in case an error occurred during a check. This is an object containing `type`, `value` and `traceback` keys.

*************************
data
*************************
The data key of a result contains an object in which you will find any key-values passed to the `check50.data` api call. The purpose of this is to provide a simple mechanism for communicating any additional data to the results. You could leverage this to for instance communicate runtime or memory usage. check50 itself does not add anything to `data` by default.


error
*************************
If check50 errored, you will find the error key containing an object as on of the top-level keys in the json. The object will always contain the following four keys:

1. **type** telling you the type of the exception.
2. **value** contains the message of the exception.
3. **traceback** is a stack trace of the exception as a list of strings.
4. **data** is an object containing any additional data the exception may carry in its payload attribute.
