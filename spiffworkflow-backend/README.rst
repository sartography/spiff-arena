Spiffworkflow Backend
==========
|Tests| |Codecov| |pre-commit| |Black|

.. |Tests| image:: https://github.com/sartography/spiff-arena/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/sartography/spiff-arena/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/sartography/spiff-arena/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/sartography/spiff-arena
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black



Features
--------

* Backend API portion of the spiffworkflow engine webapp


Running Locally
---------------

See detailed instructions at the root of spiff-arena, but:

* Install libraries using poetry:

.. code:: console

   $ poetry install

NOTE: Mysql and Postgres may require special binary files exist on your system prior
to installing these libraries. Please see the `PyPi mysqlclient instructions`_
and the pre-requisites for the `Postgres psycopq2 adapter`_ Following the
instructions here carefully will assure your OS has the right dependencies
installed.

* Setup the database - uses mysql and assumes server is running by default:

.. code:: console

   $ ./bin/recreate_db clean

* Run the server:

.. code:: console

   $ ./bin/run_server_locally


Requirements
------------

* Python 3.10+
* Poetry


Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------

This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/sartography/spiffworkflow-arena/issues
.. github-only
.. _PyPi mysqlclient instructions: https://pypi.org/project/mysqlclient/
.. _Postgres psycopq2 adapter: https://www.psycopg.org/docs/install.html#prerequisites
