import io
import re
from typing import Any
from unittest.mock import patch

import pytest
from pypdf import PdfReader

from connector_archive.report_pdf import _render_label_value_rows
from connector_archive.report_pdf import _ReportDocument
from connector_archive.report_pdf import render_report_pdf


@pytest.mark.parametrize("fallback_font", [False, True])
@pytest.mark.parametrize(
    "location", ["metadata", "label", "rows", "table", "multiple_values", "heading", "empty_heading", "filename"]
)
def test_oversized_values_are_fully_rendered(
    location: str, fallback_font: bool, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    if fallback_font:
        monkeypatch.setenv("CONNECTOR_ARCHIVE_FONT_DIR", str(tmp_path))
    tokens = [f"TOKEN{index:04d}" for index in range(1000)]
    value = " ".join(tokens)
    report: dict[str, Any] = {"title": "Long report", "metadata": [], "sections": []}
    files = []
    if location == "metadata":
        report["metadata"] = [["Before", "before marker"], ["Notes", value], ["After", "after marker"]]
    elif location == "label":
        report["metadata"] = [[value, "after marker"]]
    elif location == "rows":
        # Lists are formatted with newlines, which must also survive the paragraph fallback.
        report["sections"] = [{"rows": [["Before", "before marker"], ["Notes", tokens], ["After", "after marker"]]}]
    elif location == "table":
        report["sections"] = [
            {
                "columns": ["ID", "Notes"],
                "column_widths": [1, 9],
                "rows": [[1, "before marker"], [2, value], [3, "after marker"]],
            }
        ]
    elif location == "multiple_values":
        report["sections"] = [{"columns": ["First", "Second"], "rows": [[value, value.replace("TOKEN", "OTHER")]]}]
    elif location in ("heading", "empty_heading"):
        report["sections"] = [{"columns": [value, "Notes"], "rows": [[1, "after marker"]] if location == "heading" else []}]
    else:
        files = [{"original_filename": value, "size": 123, "sha256": "a" * 64}]

    pdf = PdfReader(io.BytesIO(render_report_pdf(report, files)))
    assert len(pdf.pages) > 1
    text = "\n".join(page.extract_text() for page in pdf.pages)
    assert re.findall(r"TOKEN\d{4}", text) == tokens
    assert "Archived files" in text
    if location in ("metadata", "rows", "table"):
        assert text.index("before marker") < text.index(tokens[0])
        assert text.index(tokens[-1]) < text.index("after marker")
    if location == "multiple_values":
        assert re.findall(r"OTHER\d{4}", text) == [token.replace("TOKEN", "OTHER") for token in tokens]
    if location == "empty_heading":
        assert "None" in text
    if location == "filename":
        assert "a" * 64 in text.replace("\n", "")


def test_unbroken_oversized_value_is_not_truncated() -> None:
    value = "0123456789" * 2000
    pdf = render_report_pdf({"metadata": [["Long value", value]]}, [])
    text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
    assert "".join(re.findall(r"\d{10,}", text)) == value


def test_heading_and_row_together_must_fit_on_a_page() -> None:
    heading = "\n".join(f"HEADING{index:03d}" for index in range(45))
    value = "\n".join(f"VALUE{index:03d}" for index in range(15))
    report = {"sections": [{"columns": [heading], "rows": [[value]]}]}
    pdf = PdfReader(io.BytesIO(render_report_pdf(report, [])))
    text = "\n".join(page.extract_text() for page in pdf.pages)
    assert re.findall(r"HEADING\d{3}", text) == heading.splitlines()
    assert re.findall(r"VALUE\d{3}", text) == value.splitlines()


def test_short_rows_keep_their_table_layout_around_long_values() -> None:
    document = _ReportDocument("Test", "2026-01-01")
    document.add_page()
    document.use_font(9)
    with patch.object(document, "table", wraps=document.table) as table:
        _render_label_value_rows(
            document,
            [["Before", "short value"], ["Long", "long value " * 5000], ["After", "short value"]],
        )
    assert table.call_count == 2
    for call in table.call_args_list:
        assert call.kwargs["col_widths"] == (35, 65)
        assert call.kwargs["borders_layout"] == "HORIZONTAL_LINES"
        assert call.kwargs["first_row_as_headings"] is False
