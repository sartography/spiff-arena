# connector-archive

Archive one process run for auditors.

`archive/ArchiveToS3` writes these objects under `key_prefix` in an S3 (or S3-compatible) bucket:

- `files/NNN-<filename>`: each uploaded file
- `summary.pdf`: the `report` parameter rendered as a PDF, plus a table of the archived files with SHA-256 values
- `manifest.json`: keys, sizes, and SHA-256 values for everything above. It is deleted after the first upload works and written last, so if it is present the archive is complete.

The keys are the same each time for the same `key_prefix`, so you can retry a failed task.
The command runs archive preparation and S3 work in a supervised process with a 40-second deadline, before the backend stops waiting (45 seconds).
At the deadline it terminates the worker (including any in-flight PUT/DELETE, SDK retry, or retry backoff) and returns an error, allowing up to two seconds for worker cleanup. Retry the task.
Each S3 request also has a 5 second connect timeout, a 15 second read timeout, and up to two retries; all share the command-wide budget.
Stopping the worker cannot undo a request S3 has already received: a timed-out request may still have been committed by S3. A retry writes the same keys.
All files are held in memory while the archive is built. There is no size limit.

The credentials need `s3:PutObject` and `s3:DeleteObject` on the bucket. Turn on bucket versioning, so a retry never loses an earlier copy.

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
