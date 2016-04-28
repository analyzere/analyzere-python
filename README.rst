Analyze Re Python Client |travis|
=================================

This is a Python wrapper for a Analyze Re REST API. It allows you to easily
utilize the PRIME Re platform in your applications.

.. |travis| image:: https://travis-ci.org/analyzere/analyzere-python.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/analyzere/analyzere-python

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

Publishing
----------

1. Install `twine <https://pypi.python.org/pypi/twine>`_ and
   `wheel <https://pypi.python.org/pypi/wheel>`_::

    pip install twine wheel

2. Increment version number in ``setup.py`` according to
   `PEP 440 <https://www.python.org/dev/peps/pep-0440/>`_.

3. Commit your change to ``setup.py`` and create a tag for it with the version
   number. e.g.::

    git tag 0.5.1
    git push origin 0.5.1

4. Register the package::

    python setup.py register

5. Package source and wheel distributions::

    python setup.py sdist bdist_wheel

6. Upload to PyPI with twine::

    twine upload dist/*
