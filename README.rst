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

Package Management
---------------------

The Analyze Re Python Client uses `Poetry <https://python-poetry.org/>`_ for
package and dependency management. Poetry can be easily installed
using either `pip` or `conda`.

Testing
-------

`poetry run pytest` (or) `poetry run py.test`

Increment version
-----------------

If you are going to publish a new version increment the version number in the `pyproject.toml` file.

Testing Publication
-------------------

`poetry build`

`poetry config repositories.testpypi https://test.pypi.org/legacy/`

`poetry publish --repository testpypi`

Publishing
----------

`poetry build`

`poetry publish`
