# connector-archive

Archive one process run for auditors.

`archive/ArchiveToS3` writes these objects under `key_prefix` in an S3 (or S3-compatible) bucket:

- `files/NNN-<filename>`: each uploaded file
- `summary.pdf`: the `report` parameter rendered as a PDF, plus a table of the archived files with SHA-256 values
- `manifest.json`: object keys, S3 version IDs, sizes, and SHA-256 values; published last to mark a complete archive

## Storage requirements

Bucket versioning must be enabled and remain enabled. S3-compatible endpoints must support versioning and return
non-`null` version IDs for new uploads. The command rejects unversioned buckets and uploads without these IDs.

The connector credentials need:

- `s3:GetBucketVersioning` on the bucket
- `s3:GetObject`, `s3:GetObjectVersion`, and `s3:PutObject` on the archive objects

Keep all referenced object versions. Deleting versions or expiring noncurrent versions can break published archives.

## Retries and concurrent uploads

Retries write to the same keys for the same `key_prefix`. Each upload creates an immutable S3 object version, and the
version 2 manifest records the exact versions of the files and summary. Concurrent workers can overwrite the current
keys without changing the versions referenced by a published manifest.

The manifest is replaced in one atomic S3 PUT after all uploads succeed. The last publication wins. A failed retry
leaves the previous complete manifest readable, even when the retry contains different or fewer files.

## Reading an archive

Always read objects using the version IDs in the manifest, not the current keys alone. For example:

```python
for file in manifest["files"]:
    response = s3.get_object(Bucket=bucket, Key=file["archive_key"], VersionId=file["version_id"])
```

For the summary, use `manifest["summary"]["key"]` and its `version_id`.
Readers need `s3:GetObject` for the current manifest and `s3:GetObjectVersion` for pinned versions.

The command response includes `summary_version_id`, `manifest_version_id`, and a `version_id` for each entry in
`objects`. Use these to read that command's completed archive even if another worker publishes later.

## Timeouts and memory

Archive preparation and S3 work run in a supervised process with a 40-second deadline, before the backend stops
waiting at 45 seconds. At the deadline, the command stops the worker—including in-flight S3 calls and retry
backoff—and returns an error. Worker cleanup can take up to two additional seconds. Retry the failed task.

Each S3 request also has a 5-second connect timeout, a 15-second read timeout, and up to two retries, all within the
command-wide budget. Stopping the worker cannot undo a request S3 has already received; a timed-out request may
still be committed by S3.

All files are held in memory while the archive is built. There is no size limit.

## Upgrading existing archives

Stop old connector workers before rollout; they do not pin object versions.

Before overwriting any files, the connector upgrades an existing version 1 manifest by capturing each object's
version and verifying its size and checksum. Objects created before bucket versioning use S3's addressable `null`
version. If the legacy archive is already inconsistent, the command fails without uploading new files. Restore
that archive before retrying.

## PDF rendering

Short metadata and table rows keep their table layout. Rows too tall to fit on a page are rendered as labeled,
page-breakable paragraphs so long values are included in full. This also applies to table headings and attachment names.

The PDF uses DejaVu Sans from `/usr/share/fonts/truetype/dejavu` (the `fonts-dejavu-core` package in the Docker image),
or from the directory in `CONNECTOR_ARCHIVE_FONT_DIR`. Without it, the PDF uses a built-in font, and characters
outside latin-1 become `?`.

## Parameters

- `bucket`, `region`, `endpoint_url` (optional, for S3-compatible storage)
- `aws_access_key_id`, `aws_secret_access_key`: use secret references such as `"secret:archive_aws_secret_access_key"`
- `key_prefix`: for example `"r2r/project-accounting-provisions/" + str(process_instance_id)`
- `report`: `{"title": str, "metadata": [[label, value], ...], "sections": [...]}`. A section is one of these:
  - `{"heading": str, "rows": [[label, value], ...]}`
  - `{"heading": str, "columns": [...], "rows": [[...], ...]}`
  - `{"heading": str, "text": str}`
- `files`: use `get_process_instance_files(include_contents=True)` in the parameter expression so the file contents
  never go into task data. Plain data URL strings also work.
