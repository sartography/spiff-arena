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

## Model source providers

An extension can register a provider at `app.extensions["model_sources"]` to
supply instance-specific model inputs. The `ModelSourceProvider` protocol in
`services/model_sources.py` defines three methods:

- `open(session, instance)` returns a file set for an existing instance, or `None`
  to use Arena's repository/Git behavior.
- `prepare(session, instance)` prepares a new instance's file set in the caller's
  transaction. Arena flushes the instance first, then compiles the supplied bytes
  and persists definitions without committing. Providers must not commit either.
- `assert_can_migrate(session, instance)` raises if the provider cannot support
  version migration for the instance.

A file set implements `paths()` (repository-relative paths) and `read(path)`
(bytes). It must include the root model configuration and all called-model
BPMN/DMN dependencies. Arena handles parsing, task-owned form resolution, and
API responses. Once a file set is selected, missing files raise
`FileNotFoundError`; they must not silently fall back to another source.
Provider failures propagate rather than selecting the repository as a fallback.
Unpersisted instances and deployments without a provider use the repository.
Without a provider, creation commits requested repository definitions before
adding the new instance; `commit_db=False` leaves the instance and queue work
uncommitted, not those definitions.

This executes **trusted deployment code**, not sandboxed process-author code.
Control who can edit enabled packages. This is separate from BPMN extensions,
which execute workflows through the extensions API.
