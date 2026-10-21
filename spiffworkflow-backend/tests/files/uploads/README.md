# Upload regression fixtures

Synthetic files with no customer data, generated for the upload/review tests:

- `image.png`: 10 × 10 solid-color RGB PNG.
- `sheet.xlsx`: one sheet, A1 = `Upload round trip`, B2 = `123.45`.
- `document.docx`: one paragraph, `Upload round trip`.

To regenerate in this directory (test/runtime dependencies are unchanged):

```bash
uv run --no-project --with pillow --with openpyxl --with python-docx python - <<'PY'
from PIL import Image
from openpyxl import Workbook
from docx import Document

Image.new('RGB', (10, 10), (31, 120, 200)).save('image.png')
workbook = Workbook()
workbook.active['A1'] = 'Upload round trip'
workbook.active['B2'] = 123.45
workbook.save('sheet.xlsx')
document = Document()
document.add_paragraph('Upload round trip')
document.save('document.docx')
PY
```

The test compares downloaded bytes with the checked-in files, not a fixed hash.
The process fixture is `tests/data/file_upload_review/`: upload → generate
Markdown link → manual review → read-only form review.
