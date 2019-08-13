.. _extension_writer:

Writing check50 extensions
==========================

Core to check50's design is extensibility. Not only in checks, but also in the tool itself. We designed :code:`check50.c`, :code:`check50.py` and :code:`check50.flask` to be extensions of check50 that ship with check50. By design these three modules are all standalone and only depend on the core of check50, and no other part of check50 depends on them. In other words, you can remove or add any of these modules and check50 would still function as expected.

We ship check50 with three extensions because these extensions are core to the material cs50 teaches. But different courses have different needs, and we realize we cannot predict and cater for every usecase. This is why check50 comes with the ability to `pip install` other Python packages. You can configure this via the :code:`dependencies` key in :code:`.cs50.yaml`. Through this mechanism you can write your own extension and then have check50 install it for you whenever check50 runs. Host your extension anywhere `pip` can install from, for instance GitHub or PyPi. And all you have to do then is to fill in the :code:`dependencies` key of :code:`.cs50.yaml` with the location of your extension. check50 will make sure your extension is always there when the checks are run.


check50.internal
*******************************

In addition to all the functionality check50 exposes, we expose an extra API for extensions in :code:`check50.internal`. You can find the documentation in :ref:`api`.


Example: a JavaScript extension
*******************************
Out of the box check50 does not ship with any JavaScript specific functionality. You can use check50's generic API and run a :code:`.js` file through an interpreter such as :code:`node`: :code:`check50.run('node <student_file.js>')`. But we realize most JavaScript classes are not about writing command-line scripts, and we do need a way to call functions. This is why we wrote a small javascript extension for check50 dubbed check50_js at
https://github.com/cs50/check50/tree/sample-extension.


*******************************
check50_js
*******************************
The challenge in writing this extension is that check50 itself is written in Python, so we need an interface between the two languages. This could be as simple as an intermediate JavaScript script that runs the students function and then outputs the results to stdout for check50 to read. But this approach does create indirection and creates quite some clutter in the checks codebase. Luckily, in case of Python and JavaScript (and PHP and Perl) we have access to a Python package called :code:`python-bond`. This package lets us "bond" two languages together, and lets you evaluate code in another language's interpreter. Effectively creating a channel through which you can evaluate code and call functions from the other language. This is what we ended up doing for our JavaScript extension.

You can find example checks using check50_js and their solutions at:

* **hello.js**: `checks <https://github.com/cs50/check50/tree/examples/js/hello>`__ `solution <https://github.com/cs50/check50/tree/examples/solutions/hello_js/hello.js>`__
* **line.js**: `checks <https://github.com/cs50/check50/tree/examples/js/line>`__ `solution <https://github.com/cs50/check50/tree/examples/solutions/line_js/line.js>`__
* **addition.js**: `checks <https://github.com/cs50/check50/tree/examples/js/addition>`__ `solution <https://github.com/cs50/check50/tree/examples/solutions/addition_js/addition.js>`__


To try any of these examples for yourself, simply run:

* **hello.js**:

.. code-block:: bash

  wget https://raw.githubusercontent.com/cs50/check50/examples/solutions/hello_js/hello.js
  check50 cs50/check50/examples/js/hello

* **line.js**:

.. code-block:: bash

  wget https://raw.githubusercontent.com/cs50/check50/examples/solutions/line_js/line.js
  check50 cs50/check50/examples/js/line

* **addition.js**:

.. code-block:: bash

  wget https://raw.githubusercontent.com/cs50/check50/examples/solutions/addition_js/addition.js
  check50 cs50/check50/examples/js/addition
