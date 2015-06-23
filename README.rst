Analyze Re Python Client
========================

This is a Python wrapper for a Analyze Re REST API. It allows you to easily
utilize the PRIME Re platform in your applications.

Installation
------------

::

   pip install analyzere

Usage
-----

Please see http://docs.analyzere.net/?python for the most up-to-date
documentation.

Testing
-------

We currently commit to being compatible with Python 2.7 and Python 3.4. In
order to run tests against against each environment we use
`tox <http://tox.readthedocs.org/>`_ and `py.test <http://pytest.org/>`_. You'll
need an interpreter installed for each of the versions of Python we test.
You can find these via your system's package manager or
`on the Python site <https://www.python.org/downloads/>`_.

To start, install tox::

    pip install tox

Then, run the full test suite::

    tox

To run tests for a specific module, test case, or single test, you can pass
arguments to py.test through tox with ``--``. E.g.::

    tox -- tests/test_base_resources.py::TestReferences::test_known_resource

See ``tox --help`` and ``py.test --help`` for more information.
