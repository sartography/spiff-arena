# Python app extensions

Deployments can explicitly enable trusted Python packages in their process-model
repository at application boot:

```sh
SPIFFWORKFLOW_BACKEND_APP_EXTENSIONS='["example"]'
```

Arena loads `<prefix>/<name>/__init__.py` beneath
`SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR`, where `<prefix>` is
`SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX` (default: `extensions`).
It calls `init_app(app)` after initializing the database integration. Packages
support relative imports. Install any additional dependencies in the deployment
environment.

Python app extensions share this directory prefix with BPMN/UI extensions, but
have their own explicit enable list above; they do not require
`SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED`. For example, setting the prefix to
`custom/extensions` loads `custom/extensions/example/__init__.py`, not
`extensions/example/__init__.py`. There is no fallback to the default directory.
The prefix must be a nonempty repository-relative directory, not the repository
root. Absolute paths, `..` traversal, and symlinks escaping the repository are
rejected when Python app extensions are enabled.

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

## Initialization lifecycle and ordering

The app factory calls `setup_config`, `db.init_app`, `migrate.init_app`, then
`init_app_extensions`, in that order. The database engine is available at this
point, but no connection is opened or schema migration run by those initialization
calls. Access Flask context-dependent APIs inside `with app.app_context():`.
Database URI and engine options have already been consumed; an initializer cannot
reconfigure the existing engine by changing those settings.

Initializers run in configured list order, with no automatic dependency sorting.
If one initializer depends on another's registrations, list its dependency first.
Keep module imports free of side effects and use `init_app(app)` to register the
extension's hooks and providers.

This is an early registration hook, not an "application fully ready" hook.
Celery, the background-job publisher, scheduler, and some logging/error handling
services are initialized afterward. Do not assume they are available, or start
background work that depends on unfinished setup. Initializers can also run
before worker processes fork; take care with process-local resources.

API processes, workers, and Flask CLI commands all create apps. Initializers must
therefore account for multiple app instances and command-line use, including
schema migration commands. Document each extension's dependencies, configuration,
setup/migration requirements, and operational behavior alongside its package in
the process-model repository.

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
BPMN/DMN dependencies. Repository inputs and provider-supplied inputs share Arena's
BPMN/DMN compilation and validation pipeline. Repository loading can discover
additional called-model files; provider-supplied inputs form a complete set.
Arena also handles task-owned form resolution and API responses. Once selected, a file set is authoritative: missing files raise
`FileNotFoundError`, and provider failures propagate to the caller.
Unpersisted instances and deployments without a provider use the repository.
For repository-backed creation, Arena commits requested definitions before adding
the new instance. With `commit_db=False`, the caller owns the subsequent commit
for the instance and queue work.

App extensions run with the backend application's privileges. Limit write access
to enabled packages to trusted deployment maintainers.

BPMN extensions execute workflows through the extensions API; Python app
extensions initialize packages at application boot.
