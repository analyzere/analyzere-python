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

We currently commit to being compatible with Python 2.7. 3.4, 3.5, and 3.6. In
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

Tagging
----------

1. Install `twine <https://pypi.python.org/pypi/twine>`_ and
   `wheel <https://pypi.python.org/pypi/wheel>`_::

    pip install twine wheel

2. Increment version number in ``setup.py`` according to
   `PEP 440 <https://www.python.org/dev/peps/pep-0440/>`_.

3. Increment the version number in the ``user_agent`` variable in
   ``analyzere/__init__.py``.

4. Commit your change to ``setup.py`` and create a tag for it with the version
   number. e.g.::

    git tag 0.5.1
    git push origin 0.5.1

``.pypirc`` file
-----------------

Create a ``.pypirc`` file with your production and test server accounts in your
``HOME`` directory. This file should look as follows:

::

    [distutils]
    index-servers=
        pypi
        testpypi

    [testpypi]
    repository = https://test.pypi.org/legacy/
    username = <username>
    password = <password>

    [pypi]
    repository = https://upload.pypi.org/legacy/
    username = <username>
    password = <password>


Note that ``testpypi`` and ``pypi`` require separate registration.

Testing Publication
-------------------

1. Ensure you have tagged the master repository according to the tagging
instructions above.

2. Package source and wheel distributions::

    python setup.py sdist bdist_wheel

3. Check format::

    twine check dist/*

4. Upload to PyPI with twine::

    twine upload dist/* -r testpypi

5. Test that you can install the package from testpypi::

    pip install -i https://testpypi.python.org/pypi analyzere

Publishing
-----------

1. Ensure you have tagged the master repository according to the tagging
instructions above, testing publication before publication.

2. Package source and wheel distributions::

    python setup.py sdist bdist_wheel

3. Upload to PyPI with twine::

    twine upload dist/* -r pypi
