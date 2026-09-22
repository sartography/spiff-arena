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

## Optional process model history

An extension can preserve the exact source files used to create each process
instance. Register a session-accepting factory at
`app.extensions["process_model_history"]`.

Arena calls `capture(instance_id, model_id)` for a new persistent instance. It
stores the source files and returns executable specifications built from those
same bytes. Capture and definition persistence use the caller's transaction.
Uninitialized persistent runtimes and reserved asynchronous message starts use
`specs(instance_id, model_id, process_id)` to reload specifications from the
archive.

For an existing instance, Arena calls `has_snapshot(instance_id)`. If it
returns false, Arena follows its standard repository and Git behavior. This
allows instances created before an archive was enabled to continue working.
Ephemeral workflows and deployments without a provider also keep standard
behavior.

Authenticated instance GETs delegate diagram/metadata fields to
`instance_payload(instance_id, model_id, process_id)` and individual file
responses to `file_payload(instance_id, path)`. Form schemas and UI schemas use
`task_file(instance_id, owning_process_id, filename)`; missing files return an
unavailable error rather than falling back to current files. The provider owns
capture, storage, parsing, source resolution, response construction and schema
validation. Core migrations add no history tables or columns.

Clients can pass a repository-relative `source_file_path` query parameter to
either authorized instance GET variant. The history provider returns the file in
`source_file`, encoded as UTF-8 or base64 with its content type. Historical task
forms do not require the owning process model or called model to remain in the
live repository.

Version migration/checks are explicitly rejected for instances that have a source
snapshot because target selection and atomic source replacement remain
unimplemented. Instances without a snapshot retain standard migration behavior.
Runtime model metadata and backfill are not part of this integration. Deployments
must run the extension-owned, versioned migration runner before enabling it on all
API/worker writers. The provider must not claim an instance unless it has a
complete snapshot.