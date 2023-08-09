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

`pytest` or `py.test`

Increment version
-----------------

If you are going to publish a new version increment the version number in the `pyproject.toml` file.

Testing Publication
-------------------

`poetry build`
`poetry config.repositories.testpypi https://test.pypi.org`
`poetry publish --repository testpypi`

Publishing
----------

`poetry build`

`poetry publish`
