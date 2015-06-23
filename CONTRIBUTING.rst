Contributing
============

Contributions are always welcome and credit will be given.

Bug reports
===========

When `reporting a bug <https://github.com/analyzere/analyzere-python/issues>`_
please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in
      troubleshooting.
    * Detailed steps to reproduce the bug.

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at
https://github.com/analyzere/analyzere-python/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible to make it easier to review and
  implement.

Development
===========

To set up `analyzere-python` for local development:

1. `Fork analyzere-python on GitHub
   <https://github.com/analyzere/analyzere-python/fork>`_.
2. Clone your fork locally::

    git clone git@github.com:your_name_here/analyzere-python.git

3. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

4. When you're done making changes, run the test suite with
   `tox <http://tox.readthedocs.org/en/latest/install.html>`_::

    tox

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

6. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code, open
a pull request and indicate that it is a work-in-progress.

For merging, you should:

1. Include passing tests (run ``tox``).
2. Add yourself to ``AUTHORS``.
