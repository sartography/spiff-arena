# connector-archive

Archive one process run for auditors.

`archive/ArchiveToS3` writes these objects under `key_prefix` in an S3 (or S3-compatible) bucket:

- `files/NNN-<filename>`: each uploaded file
- `summary.pdf`: the `report` parameter rendered as a PDF, plus a table of the archived files with SHA-256 values
- `manifest.json`: keys, sizes, and SHA-256 values for everything above. It is deleted after the first upload works and written last, so if it is present the archive is complete.

The keys are the same each time for the same `key_prefix`, so you can retry a failed task.
The command stops starting new uploads after 40 seconds, before the backend stops waiting (45 seconds), and returns an error. Retry the task.
Each S3 request has a 5 second connect timeout, a 15 second read timeout, and one retry. One slow upload can still go past 45 seconds; the backend then marks the task as failed, and a retry writes the same keys.
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
