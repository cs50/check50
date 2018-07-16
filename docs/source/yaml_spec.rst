.. _yaml_spec:

Check50 in .cs50.yaml
======================
Check50, and other CS50 tools like submit50 and lab50, use a special configuration file called ``.cs50.yaml``. Here follows the spec of all configuration options for check50 in ``.cs50.yaml``.

Specify just that this is a valid slug for check50. This configuration will allow you to run ``check50 <slug>``, by default ``check50`` will look for an ``__init__.py`` containing Python checks.

checks:
*******

``checks:`` takes either a truthy value to indicate that this slug is valid for check50, or a filename specifying a filename containing check50 Python checks, or a record of check50 YAML checks.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true

Only specifies that this is a valid slug for check50. This configuration will allow you to run ``check50 <slug>``, by default ``check50`` will look for an ``__init__.py`` containing Python checks.

.. code-block:: YAML
    :linenos:

    check50:
      checks: "my_filename.py"

Specifies that this is a valid slug for check50, and has check50 look for ``my_filename.py`` instead of ``__init__.py``.

.. code-block:: YAML
    :linenos:

    check50:
      checks:
        hello world:
          - run: python3 hello.py
            stdout: Hello, world!
            exit: 0

Specifies that this is a valid slug for check50, and has check50 compile and run the YAML check. For more on YAML checks in check50 see :ref:``check_writer``.

exclude:
********

``exclude:`` takes a list of patterns. These patterns are globbed and any matching files are excluded. If a pattern starts with ``!``, all files are included instead. The last item in the list wins. If and only if a pattern does not contain a ``/``, and starts with a ``*``, it is considered recursive in such a way that ``*.o`` will exclude all files in any directory ending with ``.o``. This special casing is just for convenience. Alternatively you could write ``**/*.o`` that is functionally identical to ``*.o``, or write ``./*.o`` if you only want to exclude files ending with ``.o`` from the top-level directory.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      exclude:
        - "*.pyc"

Excludes all files ending with ``.pyc``.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      exclude:
        - "*"
        - "!*.py"

Exclude all files, but include all files ending with ``.py``. Note that order is important here, if you would inverse the two lines it would read: include all files ending with ``.py``, exclude everything. Effectively excluding everything!

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      exclude:
        - "*"
        - "!source/"

Exclude all files, but include all files in the source directory.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      exclude:
        - "build/"
        - "docs/"

Include everything, but exclude everything in the build and docs directories.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      exclude:
        - "*"
        - "!source/"
        - "!*.pyc"

Exclude everything, include everything from the source directory, but exclude all files ending with ``.pyc``.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      exclude:
        - "source/**/*.pyc"

Include everything, but any files ending on ``.pyc`` within the source directory. The ``**`` here pattern matches any directory.

required:
*********

``required:`` takes a list of filenames that are required. If any such file are not present when checking, check50 will report that the file is missing and not run any checks. ``required:`` takes precedence over ``exclude:``, thus any files in ``required:`` are always included.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      required:
        - "foo.py"
        - "bar.c"

Require that both foo.py and bar.c are present and include them.

dependencies:
*************

``dependencies:`` is a list of ``pip`` installable dependencies that check50 will install.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      dependencies:
        - pyyaml
        - flask

Has check50 install both ``pyyaml`` and ``flask`` via ``pip``.

.. code-block:: YAML
    :linenos:

    check50:
      checks: true
      dependencies:
        - git+https://github.com/cs50/submit50#egg=submit50

Has check50 ``pip install`` submit50 from GitHub, especially useful for projects that are not hosted on PyPi. See https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support for more info on installing from a VCS.
