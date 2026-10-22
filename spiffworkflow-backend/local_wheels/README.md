# Local Wheels

To test a local wheel, copy it into this folder and run from `spiffworkflow-backend/`:

```
uv add local_wheels/my.whl
```

For a temporary install without changing project dependencies:

```
uv sync
uv pip install --python .venv/bin/python local_wheels/*.whl
```

Start the backend with `uv run --no-sync` to preserve the temporary install.
