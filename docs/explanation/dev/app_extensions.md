# Python app extensions

Deployments can explicitly enable trusted Python packages in their process-model
repository at application boot:

```sh
SPIFFWORKFLOW_BACKEND_APP_EXTENSIONS='["example"]'
```

Arena loads `extensions/<name>/__init__.py` beneath
`SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR` and calls `init_app(app)` after
initializing the database integration. Packages can use relative imports without
changing `PYTHONPATH` or building a custom Dockerfile. Any additional dependencies
must already be installed.

```python
# extensions/example/__init__.py
from .provider import Provider


def init_app(app):
    app.extensions["example"] = Provider
```

Initializers run in configured order, once per app creation (including workers),
and own their validation and registration. An empty list, the default, loads
nothing. Missing packages or initialization errors fail application startup.
Names must be Python identifiers; duplicates and paths escaping the configured
repository package are rejected. No repository scanning or automatic discovery
occurs. Packages receive private module identities to isolate relative imports
between app instances.

This executes **trusted deployment code**, not sandboxed process-author code.
Control who can edit enabled packages. This is separate from BPMN extensions,
which execute workflows through the extensions API.
