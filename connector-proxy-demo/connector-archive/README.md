# connector-archive

Archive a process run's uploaded files and summary PDF to S3 or S3-compatible storage.

`archive/ArchiveToS3` writes these objects under `key_prefix`:

- `files/NNN-<filename>`: uploaded files
- `summary.pdf`: the structured `report`, plus file names and SHA-256 checksums
- `manifest.json`: object keys, S3 version IDs, sizes, and checksums; published last to mark a complete archive

## Storage requirements

Keep bucket versioning enabled. The command rejects unversioned buckets and uploads without non-`null` version IDs,
including on S3-compatible endpoints.

Connector permissions:

- `s3:GetBucketVersioning` and `s3:ListBucket` on the bucket
- `s3:GetObject`, `s3:GetObjectVersion`, and `s3:PutObject` on archive objects

`s3:ListBucket` lets S3 distinguish a missing manifest from denied access.
Readers need `s3:GetObject` for the current manifest and `s3:GetObjectVersion` for referenced versions.
Do not delete or expire referenced versions; doing so breaks archives.

## Retries and concurrent uploads

Retries reuse the same keys. Each upload creates an immutable object version, and the version 2 manifest records
which versions belong together. Concurrent uploads cannot change the versions referenced by a published manifest.

The manifest is replaced atomically after all uploads succeed; the last publication wins. Failed retries leave the
previous complete archive readable, even when the retry contains different or fewer files.

## Reading an archive

Use each manifest entry's `version_id`, not its current key alone:

```python
for file in manifest["files"]:
    response = s3.get_object(Bucket=bucket, Key=file["archive_key"], VersionId=file["version_id"])
```

For the summary, use `manifest["summary"]["key"]` and its `version_id`.
The command response also includes `summary_version_id`, `manifest_version_id`, and a `version_id` for each item in
`objects`. These identify that command's archive even if another worker publishes later.

## Timeouts and memory

A supervised worker handles archive preparation, uploads, and response transfer within a 40-second deadline.
At the deadline, the command stops the worker and returns an error. Cleanup can take two additional seconds,
within the backend's default 45-second timeout. Retry the failed task.

S3 calls also have a 5-second connect timeout, a 15-second read timeout, and up to two retries, all within the same
budget. A timed-out request may still be committed by S3; stopping the worker cannot undo it.

All files are held in memory while building the archive. There is no size limit.

## Upgrading existing archives

Stop old connector workers before rollout; they do not pin object versions.

Before overwriting files, the connector upgrades version 1 manifests by capturing and checksum-verifying each
object's version. Objects predating bucket versioning use S3's addressable `null` version. If the existing archive
is inconsistent, the command fails without uploading new files. Restore that archive before retrying.

## PDF rendering

Short rows retain their table layout. Oversized rows become labeled, page-breakable paragraphs without truncation.
This also applies to table headings and attachment names.

The PDF uses DejaVu Sans from `CONNECTOR_ARCHIVE_FONT_DIR` or `/usr/share/fonts/truetype/dejavu` (included in the
Docker image). Without it, common Unicode punctuation is approximated and other characters outside Latin-1 become `?`.

## Parameters

- `bucket`: destination bucket
- `key_prefix`: archive path, for example `"archives/" + str(process_instance_id)`
- `aws_access_key_id`, `aws_secret_access_key`: use secret references such as `"secret:archive_aws_secret_access_key"`
- `report`: `{"title": str, "metadata": [[label, value], ...], "sections": [...]}`. Sections support:
  - `{"heading": str, "rows": [[label, value], ...]}`
  - `{"heading": str, "columns": [...], "rows": [[...], ...], "column_widths": [...]}` (`column_widths` is optional)
  - `{"heading": str, "text": str}`
- `files` (optional): use `get_process_instance_files(include_contents=True)` directly in the service task parameter
  so contents are not stored in task data. Alternatively, pass a list of data URL strings.
- `region` (optional): defaults to `us-east-1`
- `endpoint_url` (optional): custom S3-compatible endpoint
