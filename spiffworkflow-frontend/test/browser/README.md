# Browser-based tests

To run:

    cd ~/projects/github/sartography/spiff-arena/spiffworkflow-frontend/test/browser

    # defaults
    uv run pytest

    # headed browser and slowmo for people to watch
    uv run pytest --headed --slowmo 1000

## Accessibility scans

CI runs the accessibility suite and the other browser tests in parallel, with
separate application stacks. Each suite must create the process instances and
tasks it needs rather than rely on state left by the other suite.

To run the accessibility suite independently against a running test stack:

    uv run pytest test_accessibility.py -v --tracing=retain-on-failure

Axe results are written to `test-results/axe/` and uploaded with the accessibility
job's traces. These automated checks are not a full accessibility conformance audit.
