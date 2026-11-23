# connector-archive

Archive one process run for auditors.

`archive/ArchiveToS3` writes these objects under `key_prefix` in an S3 (or S3-compatible) bucket:

- `files/NNN-<filename>`: each uploaded file
- `summary.pdf`: the `report` parameter rendered as a PDF, plus a table of the archived files with SHA-256 values
- `manifest.json`: keys, S3 version IDs, sizes, and SHA-256 values for everything above. It is replaced last, so if it is present the archive is complete.

The keys are the same each time for the same `key_prefix`, so a retry still replaces a partial archive at the same keys.
**Bucket versioning must be enabled and remain enabled.** Each upload produces an isolated, immutable object version.
The version 2 manifest pins the exact versions returned by the file and summary uploads. Concurrent workers may overwrite the
current fixed keys, but cannot change the versions referenced by an already published manifest. Publication is one atomic S3 PUT;
the last manifest publication wins. Failed retries leave the previous complete manifest readable, even with different or fewer files.

Readers must fetch each file's `archive_key` or the summary's `key` **with its `version_id`**, not the current key alone:
`get_object(Bucket=bucket, Key=item["archive_key"], VersionId=item["version_id"])`.
The command response also includes `summary_version_id`, `manifest_version_id`, and a `version_id` for each entry in `objects`,
so callers can read their own completed archive even if another worker publishes later.
Keep all referenced object versions: deleting versions or expiring noncurrent versions can break published archives.

Before rollout, stop old connector workers, which do not pin versions. Existing version 1 manifests are upgraded before any
file is overwritten: the connector captures each object's version and verifies its size and checksum before publishing a
version-pinned manifest. Objects predating bucket versioning use S3's addressable `null` version. If the legacy archive is already
inconsistent, the command fails without uploading new files; restore the legacy archive before retrying.
The command runs archive preparation and S3 work in a supervised process with a 40-second deadline, before the backend stops waiting (45 seconds).
At the deadline it terminates the worker (including any in-flight S3 call, SDK retry, or retry backoff) and returns an error, allowing up to two seconds for worker cleanup. Retry the task.
Each S3 request also has a 5 second connect timeout, a 15 second read timeout, and up to two retries; all share the command-wide budget.
Stopping the worker cannot undo a request S3 has already received: a timed-out request may still have been committed by S3. A retry writes the same keys.
All files are held in memory while the archive is built. There is no size limit.

The connector credentials need `s3:GetBucketVersioning` on the bucket and `s3:GetObject`, `s3:GetObjectVersion`, and `s3:PutObject` on its archive objects.
Readers need `s3:GetObject` for the current manifest and `s3:GetObjectVersion` for pinned versions. S3-compatible endpoints must support bucket versioning and return immutable `VersionId` values;
the command rejects unversioned buckets and uploads without a non-`null` version ID.

The PDF uses DejaVu Sans from `/usr/share/fonts/truetype/dejavu` (the `fonts-dejavu-core` package in the Docker image), or from the
directory in `CONNECTOR_ARCHIVE_FONT_DIR`. Without it, the PDF uses a built-in font, and characters outside latin-1 become `?`.

Parameters:

- `bucket`, `region`, `endpoint_url` (optional, for S3-compatible storage)
- `aws_access_key_id`, `aws_secret_access_key`: use secret references such as `"secret:archive_aws_secret_access_key"`
- `key_prefix`: for example `"r2r/project-accounting-provisions/" + str(process_instance_id)`
- `report`: `{"title": str, "metadata": [[label, value], ...], "sections": [...]}`. A section is one of these:
  - `{"heading": str, "rows": [[label, value], ...]}`
  - `{"heading": str, "columns": [...], "rows": [[...], ...]}`
  - `{"heading": str, "text": str}`
- `files`: use `get_process_instance_files(include_contents=True)` in the parameter expression so the file contents never go into task data.
  Plain data url strings also work.
