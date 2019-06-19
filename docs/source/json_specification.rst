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
*********
Assuming `check50` is able to run successfully, you will find three keys at the top level of the json output: `slug`, `results` and `version`.

* **slug** (`string`) is the slug with which check50 was run, `cs50/problems/2018/x/caesar` in the above example.
* **results** (`[object]`) is a list containing the results of each run check. More on this key below.
* **version** (`string`) is the version of check50 used to run the checks.

If check50 encounters an error while running, e.g. due to an invalid slug, the `results` key will be replaced by an `error` key containing information about the error encountered.

results
*******
If the results key exists (that is, check50 was able to run the checks successfully), it will contain a list of objects each corresponding to a check. The order of these objects corresponds to the order the checks appear in the file in which they were written. Each object will contain the following fields:

* **name** (`string`) is the unique name of the check (the literal name of the Python function specifying the check).
* **description** (`string`) is a description of the check.
* **passed** (`bool`, nullable) is `true` if the check passed, `false` if the check failed, or `null` if the check was skipped (either because the check's dependency did not pass or because the check threw some unexpected error).
* **log** (`[string]`) contains the log accrewed during the execution of the check. Each element of the list is a line from the log.
* **cause** (`object`, nullable) contains the reason that a check did not pass. If `passed` is `true`, `cause` will be `null` and `cause` will never be `null` if `passed` is not `true`. More detail about keys that may appear within `cause` below.
* **data** (`object`) contains arbitrary data communicated by the check via the `check50.data` API call. Checks could use this to add additional information such as memory usage to the results, but check50 itself does not add anything to `data` by default.
* **dependency** (`string`, nullable) is the name of the check upon which this check depends, or `null` if the check has no dependency.

*****
cause
*****
The cause key is `null` if the check passed and non-null. This key is by design an open-ended object. Everything in the `.payload` attribute of a `check50.Failure` will be put in the `cause` key. Through this mechanism you can communicate any information you want from a failing check to the results. Depending on what occurred, check50 adds the following keys to `cause`:

* **rationale** (`string`) is a stduent-facing explanation of why the check did not pass (e.g. the student's program did not output what was expected).
* **help** (`string`) is an additional help message that may appear alongside the rationale giving additional context.
* **expected** (`string`) and **actual** (`string`) are keys that always appear in a pair. In case you are expecting X as output, but Y was found instead, you will find these keys containing X and Y in the `cause` field. These appear when a check raises a `check50.Mismatch` exception.
* **error** (`object`) appears in `cause` when an unexpected error occurred during a check. It will contain the keys `type`, `value`, `traceback` and `data` with the same properties as in the top-level `error` key described below.



error
*****
If check50 encounters an unexpected error, the `error` key will replace the `results` key in the JSON output. It will contain the following keys:

* **type** (`string`) contains the type name of the thrown exception.
* **value** (`string`) contains the result of converting the exception to a string.
* **traceback** (`[string]`) contains the stack trace of the thrown exception.
* **data** (`object`) contains any additional data the exception may carry in its `payload` attribute.

