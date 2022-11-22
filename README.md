# spiff-arena

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
