``check50``
===========

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Contents:

   check50_user
   api
   json_specification
   check_writer
   extension_writer

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`api`
.. * :ref:`modindex`
.. * :ref:`search`

check50 is a tool for checking student code. As a student you can use check50 to check your CS50 problem sets or any other Problem sets for which check50 checks exist. check50 allows teachers to automatically grade code on correctness and to provide automatic feedback while students are coding.

Installation
************

First make sure you have Python 3.6 or higher installed. You can download Python |download_python|.

.. |download_python| raw:: html

   <a href="https://www.python.org/downloads/" target="_blank">here</a>

check50 has a dependency on git, please make sure to |install_git| if git is not already installed.

.. |install_git| raw:: html

   <a href="https://git-scm.com/book/en/v2/Getting-Started-Installing-Git" target="_blank">install git</a>

To install check50 under Linux / OS X:

.. code-block:: bash

    pip install check50

Under Windows, please |install_windows_sub|. Then install check50 within the subsystem.

.. |install_windows_sub| raw:: html

   <a href="https://docs.microsoft.com/en-us/windows/wsl/install-win10" target="_blank">install the Linux subsystem</a>

Usage
*******

To use check50 to check a problem, execute check50 like so:

.. code-block:: bash

    check50 <owner>/<repo>/<branch>/<check>

For instance, if you want to check |2018x_caesar| you call:

.. |2018x_caesar| raw:: html

   <a href="https://github.com/cs50/problems/tree/2018/x/caesar" target="_blank">CS50's Caesar problem from edX 2018</a>

.. code-block:: bash

    check50 cs50/problems/2018/x/caesar

You can choose to run checks locally by passing the ``--local`` flag like so:

.. code-block:: bash

    check50 --local <owner>/<repo>/<branch>/<check>

For an overview of all flags run:

.. code-block:: bash

    check50 --help

Design
*******

* **Write checks for code in code** check50 uses pure Python for checks and exposes a small Python api for common functionality.
* **Extensibility in checks** Anyone can add checks to check50 without asking for permission. In fact, here is a tutorial to get you started: :ref:`check_writer`
* **Extensibility in the tool itself** We cannot predict everything you need, nor can we cater for every use-case out of the box. This is why check50 provides you with a mechanism for adding your own code to the tool, once more without asking for permission. This lets you support different programming languages and add new functionality. Jump to :ref:`extension_writer` to learn more.
* **PaaS** check50 can run online. This guarantees a consistent environment and lets you check code for correctness without introducing your own hardware.

Checks
*******
In check50 the checks are decoupled from the tool. You can find CS50's set of checks for CS50 problem sets at |cs50_checks|. If you would like to develop your own set of checks such that you can use check50 in your own course jump to  :ref:`check_writer`.

.. |cs50_checks| raw:: html

   <a href="https://github.com/cs50/problems" target="_blank">/cs50/problems</a>

Under the hood, checks are naked Python functions decorated with the ``@check50.check`` decorator. check50 exposes several functions, see :ref:`api`, that allow you to easily write checks for input/output testing. check50 comes with three builtin extensions: ``c``, ``py`` and ``flask``. These extensions add extra functionality for C, Python and Python's Flask framework to check50's core.

By design check50 is extensible. If you want to add support for other programming languages / frameworks and you are comfortable with Python please check out :ref:`extension_writer`.
