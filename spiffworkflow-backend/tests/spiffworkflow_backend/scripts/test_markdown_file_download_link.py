from urllib.parse import quote

import pytest
from flask import Flask

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.markdown_file_download_link import MarkdownFileDownloadLink


@pytest.mark.parametrize(
    "payload",
    [
        "a" * 64,
        "wrongprefix+" + "a" * 64,
        "spifffiledatadigest+" + "a" * 63,
        "spifffiledatadigest+" + "a" * 65,
        "spifffiledatadigest+" + "A" * 64,
        "spifffiledatadigest+" + "g" * 64,
        "spifffiledatadigest+" + "a" * 64 + "\n",
        "extra-spifffiledatadigest+" + "a" * 64,
    ],
)
def test_markdown_file_download_link_rejects_invalid_payload(payload: str) -> None:
    reference = f"data:application/octet-stream;name=document.txt;base64,{payload}"
    context = ScriptAttributesContext(
        task=None,
        environment_identifier="unit_testing",
        process_instance_id=42,
        process_model_identifier="group/model",
    )
    with pytest.raises(ValueError, match="Invalid file digest reference"):
        MarkdownFileDownloadLink().run(context, reference)


@pytest.mark.parametrize("encoded", [False, True])
@pytest.mark.parametrize(
    ("filename", "label"),
    [
        ("document.docx", "document.docx"),
        ("Provisions [draft.docx", r"Provisions \[draft.docx"),
        ("provisions]; version=2.docx", r"provisions\]; version=2.docx"),
        ("provisions *final*.docx", r"provisions \*final\*.docx"),
    ],
)
def test_markdown_file_download_link_preserves_filename(app: Flask, filename: str, label: str, encoded: bool) -> None:
    digest = "0123456789abcdef" * 4
    name = quote(filename, safe="") if encoded else filename
    reference = f"data:application/octet-stream;name={name};base64,spifffiledatadigest+{digest}"
    context = ScriptAttributesContext(
        task=None,
        environment_identifier="unit_testing",
        process_instance_id=42,
        process_model_identifier="group/model",
    )
    assert MarkdownFileDownloadLink().run(context, reference) == (
        f"[{label}](http://localhost/v1.0/process-data-file-download/group:model/42/{digest})"
    )
