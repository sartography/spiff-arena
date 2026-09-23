# Python app extensions

Deployments can explicitly enable trusted Python packages in their process-model
repository at application boot:

```sh
SPIFFWORKFLOW_BACKEND_APP_EXTENSIONS='["example"]'
```

Arena loads `extensions/<name>/__init__.py` beneath
`SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR` and calls `init_app(app)` after
initializing the database integration. Packages support relative imports. Install
any additional dependencies in the deployment environment.

```python
# extensions/example/__init__.py
from .provider import Provider


def init_app(app):
    app.extensions["example"] = Provider
```

Initializers run in configured order, once per app creation (including workers),
and own their validation and registration. Extensions are disabled by default;
Arena loads only the packages listed in the configuration. Missing packages or
initialization errors fail application startup. Names must be unique Python
identifiers, and package paths must stay within the configured repository.
Packages receive private module identities to isolate relative imports between
app instances.

## Model source providers

An extension can register a provider at `app.extensions["model_sources"]` to
supply instance-specific model inputs. The `ModelSourceProvider` protocol in
`services/model_sources.py` defines three methods:

- `open(session, instance)` returns a file set for an existing instance, or `None`
  to use Arena's repository/Git behavior.
- `prepare(session, instance)` prepares a new instance's file set in the caller's
  transaction. Arena flushes the instance first, then compiles the supplied bytes
  and persists definitions. The caller owns the commit for both Arena and provider
  changes.
- `assert_can_migrate(session, instance)` raises if the provider cannot support
  version migration for the instance.

A file set implements `paths()` (repository-relative paths) and `read(path)`
(bytes). It must include the root model configuration and all called-model
BPMN/DMN dependencies. Arena handles parsing, task-owned form resolution, and
API responses. Once selected, a file set is authoritative: missing files raise
`FileNotFoundError`, and provider failures propagate to the caller.
Unpersisted instances and deployments without a provider use the repository.
For repository-backed creation, Arena commits requested definitions before adding
the new instance. With `commit_db=False`, the caller owns the subsequent commit
for the instance and queue work.

App extensions run with the backend application's privileges. Limit write access
to enabled packages to trusted deployment maintainers.

BPMN extensions execute workflows through the extensions API; Python app
extensions initialize packages at application boot.
