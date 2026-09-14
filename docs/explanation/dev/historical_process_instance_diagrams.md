# Historical process instance diagrams and model files

New process instances retain the model sources used to create them. Editing,
renaming, or deleting model files does not change their BPMN diagrams, decision
tables, or form schemas. This includes BPMN called from another model and that
model's DMN and forms. The snapshot is captured when the instance is created,
including when execution is queued or deferred for a message start.

The instance's **Diagram** tab shows the saved BPMN with task status overlays.
Call-activity navigation uses the saved definition. Selecting a business-rule
task opens its saved DMN in **Model files**. The DMN viewer supports decision
tables and the decision requirements diagram and has no editing tools.
**Model files** also provides the captured BPMN, JSON schemas, UI schemas,
Markdown, scripts, images, and other source assets for viewing or downloading.
Text templates and code are displayed as source, without executing them.

If a historical diagram is unavailable, the diagram panel displays an error.
Task status and instance data remain available. The viewer never substitutes
today's model files. An instance reserved by the current API already has source
files, even before its engine workflow has initialized.

## Which files are saved

A source manifest contains exact file bytes from:

- The root model directory and the directories of transitively called models.
  This includes BPMN, DMN, JSON form schemas, JSON UI schemas, Jinja template
  sources, and supporting documents, styles, images, and other assets.
- Each participating model's `process_model.json` and existing ancestor
  `process_group.json` files.
- Explicitly declared shared assets outside those model directories.
- The configured repository-relative global scripts directory, when present,
  as source provenance.

Hidden files, symlinks, Python bytecode directories, and unrelated nested process
model directories are excluded. Mutable `JSONFileDataStore` JSON files declared
in the captured BPMN are excluded from the model directory and its ancestors.
User uploads and task data remain in their existing instance data storage.

For dynamic or shared source dependencies, declare repository-relative file
paths in `source_assets` in `process_model.json`. To exclude additional mutable
files, declare model-relative paths in `live_data_files`. For example:

```json
{
  "source_assets": ["shared/forms/address.json", "shared/images/logo.png"],
  "live_data_files": ["lookup-cache.json"]
}
```

These fields supplement the normal model configuration. They are not globs.
Paths must remain inside the model repository. Declaring an asset includes its
bytes in the archive; it does not change script execution or turn a live HTTP
URL into an archived resource. The source browser can download each archived
asset. It displays Markdown/HTML/CSS as source and does not follow their relative
links into the current repository.

Form retrieval and submission validation read the owning task's captured schema
and UI schema, including for called and embedded processes. Jinja is rendered
against the task data available at the time of the request. An exact replay of
a historical screen also requires historical task data and the original
renderer/runtime; source snapshots alone do not freeze either. Global Python
modules, installed libraries, external APIs, user/group permissions, and mutable
data stores continue to use the deployed environment. Capturing global scripts
records their source; it does not load an old Python environment for execution.

## Storage and runtime

`ModelSourceService` owns capture and historical file resolution. It reads each
source once into memory, checks for concurrent filesystem changes, and retries
if a file or directory changes during capture. BPMN and DMN parsing consumes
those captured bytes. Declared dependencies must be present when an instance is
created; a missing dependency fails creation rather than producing an incomplete
archive.

Three tables store the archive:

- `model_source_blob`: file bytes keyed by SHA-256 digest.
- `model_source_manifest`: a canonical manifest keyed by digest, containing
  paths, blob digests, sizes, media types, model configuration, parser inputs,
  and process/decision-to-file mappings.
- `model_source_version`: associations between manifests and compiled process
  definitions.

`process_instance.source_manifest_id` pins the manifest separately from
`bpmn_process_definition_id`. Identical sources share manifests and blobs across
instances. A form-only or diagram-layout change creates a new source version
without requiring a different compiled definition. Unchanged files are shared
across versions. Embedded processes share their containing BPMN source blob.

New source XML is **not** added to the data passed to SpiffWorkflow. Arena parses
captured BPMN/DMN using the normal parser and persists the normal compiled
specifications. The archive is separate from engine serialization. Deferred
starts load the pinned sources or compiled definition, and resumes use the saved
engine state. Task metadata extraction uses the saved model configuration.

Both instance GET variants expose `source_manifest_id`, `source_files`,
`decision_source_paths`, and `diagram_source_path` alongside the existing
`bpmn_xml_file_contents` field. Read a manifest member through:

```text
GET /process-instances/{model}/{instance}/source-files?path={repository-relative-path}
GET /process-instances/for-me/{model}/{instance}/source-files?path={repository-relative-path}
```

The response contains `path`, `file_contents`, `encoding` (`utf-8` or `base64`),
and `content_type`. These routes use instance access checks; the `for-me` route
also verifies the user's relationship to the instance. Paths outside the
manifest or a mismatched model/instance are rejected. Reads do not modify the
archive or backfill missing files.

## Migrations and existing instances

Deploy database migration `82efc719a603` before deploying the backend API and
workers. It creates the archive tables, adds the nullable instance manifest
reference, and adds source-version fields to migration history. It does not
infer or backfill sources for existing instances. Include all archive tables in
database backups. Archives are retained; automatic garbage collection is not
part of this change.

An explicit instance migration switches the saved definition and source manifest
together. A form-only change can also be migrated. Migration history records
both initial and target source versions, and the UI's **Revert** action selects
the original pair. API clients migrating to a saved definition can pass
`target_source_manifest_id` along with `target_bpmn_process_hash` to both the
migration check and migration endpoints. If several source versions share the
same definition, selecting only the definition hash is ambiguous and rejected.

For legacy instances:

- Older definitions containing a `bpmn_xml` snapshot still round-trip that field
  and retain their existing hashes. The compatibility converter is retained for
  those definitions; new definitions do not add the field.
- Without a source manifest or saved BPMN XML, diagrams use a strict lookup of
  the recorded git revision and saved source filename. This reads committed
  contents even at HEAD with uncommitted working-tree changes.
- Legacy forms require a recorded revision. NULL/empty revisions, missing
  commits/files, or unresolvable historical paths produce unavailable/error
  results. Current files are not used as a substitute.
- A recorded git revision cannot prove which uncommitted bytes were used by a
  legacy instance. Recovering missing sources requires independently established
  historical provenance; the system does not infer it from equivalent compiled
  definitions.
