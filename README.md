# spiff-arena

SpiffArena is a low(ish)-code software development platform for building, running, and monitoring executable diagrams.  It is intended to support Citizen Developers and help increase their ability to contribute to the software development process.  Using tools that look at lot like flow-charts and spreadsheets, it is possible to design some complex rules in a way that everyone in an organization can see and understand - and that are directly executable.

Please visit the [SpiffWorkflow website](https://www.spiffworkflow.org) for a [Getting Started Guide](https://www.spiffworkflow.org/posts/articles/get_started/) on how to run SpiffArena locally and try it out.  There are also
additional articles, videos, and tutorials about SpiffArena and it's components - SpiffWorkflow, Service Connectors, and BPMN.js extensions. 

# Contributing

This is a monorepo based on git subtrees that pulls together various
spiffworkflow-related projects. Here's an example command to push back to one
project:

    git subtree push --prefix=spiffworkflow-frontend git@github.com:sartography/spiffworkflow-frontend.git add_md_file

# run all lint checks and tests

    ./bin/run_pyl

Requires at root:
- .darglint
- .flake8
- .pre-commit-config.yaml
- pyproject.toml


License
-------
SpiffArena's main components under published under the terms of the
`GNU Lesser General Public License (LGPL) Version 3 <https://www.gnu.org/licenses/lgpl-3.0.txt>`_.

Support
-------
You can find us on `our Discord Channel <https://discord.gg/BYHcc7PpUC>`_

Commercial support for SpiffWorkflow is available from
`Sartography <https://sartography.com>`_

