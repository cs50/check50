.. check50 documentation master file, created by
   sphinx-quickstart on Wed Jun 27 13:24:24 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to check50's documentation!
===================================

.. toctree::
   :hidden:
   :maxdepth: 3
   :caption: Contents:

   api

.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`api`
.. * :ref:`modindex`
.. * :ref:`search`

.. _intro:

intro
=========

Check50 is a testing tool for checking student code. As a student you can use check50 to check your CS50 problem sets or any other Problem sets for which check50 checks exist. Check50 allows teachers to automatically grade code on correctness and to provide automatic feedback while students are coding.

Installation
************

First make sure you have Python 3.6 or higher installed. You can download Python [here](https://www.python.org/downloads/).

Check50 has a dependency on git, please make sure to [install git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) if git is not already installed.

To install check50 under Linux / OS X:

    pip install check50

Under Windows, please [install the Linux subsystem](https://docs.microsoft.com/en-us/windows/wsl/install-win10). Then install check50 within the subsystem.

Checks
*******
In Check50 the actual checks are decoupled from the tool. You can find CS50's set of checks for CS50 problem sets at [/cs50/checks](https://github.com/cs50/checks). If you would like to develop your own set of checks such that you can use check50 in your own course [jump to writing checks](#writing-checks).

Under the hood, checks are naked Python functions decorated with the ``` @check50.check``` decorator. Check50 exposes several functions, [documented below](#docs), that allow you to easily write checks for input/output testing. Check50 comes with two builtin extensions: `c` and `flask`. These extensions add extra functionality for C and Python's Flask framework to check50's core.

By design check50 is extensible. If you want to add support for other programming languages / frameworks and you are comfortable with Python please [check out writing extensions](#writing-extensions).
