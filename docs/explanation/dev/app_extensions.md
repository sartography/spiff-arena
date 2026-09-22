# Python app extensions

Deployments can explicitly enable trusted Python packages in their process-model
repository at application boot:

```sh
SPIFFWORKFLOW_BACKEND_APP_EXTENSIONS='["process_model_history"]'
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
which execute workflows through the existing extensions API.

The loader does not add lifecycle callbacks, routes, database tables, or ORM
relationships automatically. Feature-specific integrations must be implemented
separately. Extension database migrations belong to their deployment, not core
Arena migrations. Run initial database setup without extensions that require
schemas not yet installed.

## Optional process model history capability

An extension may register a session-accepting factory at
`app.extensions["process_model_history"]`. Arena calls its `capture(instance_id,
model_id)` and `specs(instance_id, model_id, process_id)` during creation, passing
captured specifications into definition persistence without an internal commit.
Uninitialized persistent runtimes also use `specs`, including deferred starts.
Reserved asynchronous message starts reload their archived specifications before
definition persistence. Ephemeral workflows and deployments without the provider
keep normal behavior.

Authenticated instance GETs delegate diagram/metadata fields to
`instance_payload(instance_id, model_id, process_id)`. Form schemas and UI schemas
use `task_file(instance_id, owning_process_id, filename)`; missing files return an
unavailable error rather than falling back to current files. The provider owns
capture, storage, parsing, source resolution and schema validation. Core migrations
add no history tables or columns. Clients can pass a repository-relative
`source_file_path` query parameter to either authorized instance GET variant. The
response includes the archived file in `source_file`, encoded as UTF-8 or base64
with its content type. Archived task forms do not require the owning process model
or called model to remain in the live repository.

Version migration/checks are explicitly rejected while this capability is enabled:
historical target selection and atomic source replacement remain unimplemented.
Archived runtime model metadata and legacy backfill are also not part of this
initial integration. Deployments must run the extension-owned, versioned migration
runner before enabling it on all API/worker writers. Do not enable it for legacy
instances expecting their missing sources to be reconstructed.
