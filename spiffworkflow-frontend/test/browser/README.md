# Browser-based tests

To run:

    cd ~/projects/github/sartography/spiff-arena/spiffworkflow-frontend/test/browser && HEADLESS=false pytest . --headed --slowmo=1000

    uv run pytest test/browser --headed --slowmo=1000

Maybe we can get this work at some point:

    uv run pytest test/browser --headed slowmo 1000
