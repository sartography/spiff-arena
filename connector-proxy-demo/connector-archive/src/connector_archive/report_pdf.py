"""Render a structured report dict into a PDF.

The report shape is generic so any process model can use it:

    {
        "title": "Project Accounting Provisions",
        "metadata": [["Process instance", 123], ["Completed", "2026-11-21 10:00 UTC"]],
        "sections": [
            {"heading": "Request", "rows": [["Accrual name", "Q3 provisions"], ...]},
            {"heading": "Reviews", "columns": ["Step", "Status", ...], "rows": [[...], ...], "column_widths": [1, 1, ...]},
            {"heading": "Notes", "text": "Free text"},
        ],
    }

A section with "columns" renders as a table with a heading row. Its optional "column_widths" sets the
relative width of each column. A section with only "rows" renders as a
label/value table. A section with "text" renders as a paragraph. The connector adds an "Archived files"
section on its own, so the PDF always lists what is next to it in the archive.
"""

import os
from datetime import UTC
from datetime import datetime
from typing import Any

from fpdf import FPDF
from fpdf.fonts import FontFace

DEFAULT_FONT_DIRS = ("/usr/share/fonts/truetype/dejavu",)
FONT_DIR_ENV_VAR = "CONNECTOR_ARCHIVE_FONT_DIR"

# Core PDF fonts only support latin-1. These are the common characters outside latin-1 that people type
# or paste into forms. Anything else becomes "?" when no unicode font is available.
LATIN1_REPLACEMENTS = str.maketrans(
    {
        "–": "-",
        "—": "-",
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "…": "...",
        "•": "*",
        " ": " ",
        "€": "EUR",
    }
)


class ReportPdfError(ValueError):
    pass


def format_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, list):
        return "\n".join(format_value(v) for v in value) if value else "-"
    return str(value)


def format_size(size_in_bytes: int) -> str:
    size = float(size_in_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:,.0f} {unit}" if unit == "B" else f"{size:,.1f} {unit}"
        size /= 1024
    return f"{size_in_bytes} B"  # pragma: no cover


class _ReportDocument(FPDF):
    def __init__(self, title: str, generated_at: str) -> None:
        super().__init__(orientation="portrait", unit="mm", format="Letter")
        self.report_title = title
        self.generated_at = generated_at
        self.font_family_name = "Helvetica"
        self.unicode_font = False
        self._register_unicode_font()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_title(self.clean(title))
        self.set_creator("SpiffWorkflow connector-archive")
        self.alias_nb_pages()

    def _register_unicode_font(self) -> None:
        font_dirs = [os.environ[FONT_DIR_ENV_VAR]] if os.environ.get(FONT_DIR_ENV_VAR) else list(DEFAULT_FONT_DIRS)
        for font_dir in font_dirs:
            regular = os.path.join(font_dir, "DejaVuSans.ttf")
            bold = os.path.join(font_dir, "DejaVuSans-Bold.ttf")
            if os.path.isfile(regular) and os.path.isfile(bold):
                self.add_font("DejaVuSans", "", regular)
                self.add_font("DejaVuSans", "B", bold)
                self.font_family_name = "DejaVuSans"
                self.unicode_font = True
                return

    def clean(self, text: str) -> str:
        if self.unicode_font:
            return text
        return text.translate(LATIN1_REPLACEMENTS).encode("latin-1", "replace").decode("latin-1")

    def use_font(self, size: float, bold: bool = False) -> None:
        self.set_font(self.font_family_name, "B" if bold else "", size)

    def footer(self) -> None:
        self.set_y(-12)
        self.use_font(7)
        self.set_text_color(110, 110, 110)
        footer_text = f"{self.report_title} - generated {self.generated_at} - page {self.page_no()} of {{nb}}"
        self.cell(0, 5, self.clean(footer_text), align="C")
        self.set_text_color(0, 0, 0)


def _cell_text(document: _ReportDocument, value: Any) -> str:
    return document.clean(format_value(value))


def _render_rows(
    document: _ReportDocument,
    rows: list,
    headings: list | None = None,
    bold_first_column: bool = False,
    empty_text: str = "None",
    **table_options: Any,
) -> None:
    """Keep ordinary rows in tables; render oversized rows as page-breakable labeled paragraphs."""
    texts = [[_cell_text(document, value) for value in row] for row in rows]
    labels = [_cell_text(document, value) for value in headings] if headings is not None else None
    weights = table_options.get("col_widths") or [1] * len(headings or rows[0])
    widths = [document.epw * weight / sum(weights) for weight in weights]
    line_height = table_options["line_height"]
    page_height = document.h - document.t_margin - document.b_margin - line_height
    bold = FontFace(emphasis="BOLD")

    def row_height(values: list[str], is_heading: bool = False) -> float:
        heights = []
        for index, (text, width) in enumerate(zip(values, widths, strict=True)):
            style = bold if is_heading or (bold_first_column and index == 0) else FontFace()
            with document.use_font_face(style):
                heights.append(float(document.multi_cell(width, line_height, text, dry_run=True, output="HEIGHT")))
        return max(heights, default=0)

    heading_height = row_height(labels, is_heading=True) if labels is not None else 0

    def render_table(batch: list[list[str]]) -> None:
        with document.table(**table_options) as table:
            if labels is not None:
                heading_row = table.row()
                for label in labels:
                    heading_row.cell(label)
            for values in batch:
                table_row = table.row()
                for index, text in enumerate(values):
                    table_row.cell(text, style=bold if bold_first_column and index == 0 else None)
            if not batch and labels is not None:
                table.row().cell(document.clean(empty_text), colspan=len(labels))

    def paragraph(text: str, is_label: bool = False) -> None:
        with document.use_font_face(bold if is_label else FontFace()):
            document.multi_cell(0, line_height, text, new_x="LMARGIN", new_y="NEXT")

    pending: list[list[str]] = []
    for values in texts:
        if heading_height + row_height(values) <= page_height:
            pending.append(values)
            continue
        if pending:
            render_table(pending)
            pending = []
        for index, text in enumerate(values):
            if labels is not None:
                paragraph(labels[index], is_label=True)
            paragraph(text, is_label=bold_first_column and index == 0)
        document.ln(2)
    if pending or (not texts and heading_height <= page_height):
        render_table(pending)
    elif not texts:
        for label in labels or []:
            paragraph(label, is_label=True)
        paragraph(document.clean(empty_text))


def _render_label_value_rows(document: _ReportDocument, rows: list) -> None:
    for row in rows:
        if not isinstance(row, list | tuple) or len(row) != 2:
            raise ReportPdfError(f"Each label/value row must be a [label, value] pair. Got: {row!r}")
    _render_rows(
        document,
        rows,
        bold_first_column=True,
        col_widths=(35, 65),
        first_row_as_headings=False,
        text_align="LEFT",
        line_height=5,
        borders_layout="HORIZONTAL_LINES",
    )


def _render_table(document: _ReportDocument, columns: list, rows: list, column_widths: list | None = None) -> None:
    heading_style = FontFace(emphasis="BOLD", fill_color=(230, 230, 230))
    if column_widths is not None and (
        len(column_widths) != len(columns) or not all(isinstance(w, int | float) and w > 0 for w in column_widths)
    ):
        raise ReportPdfError(f"column_widths must have {len(columns)} positive numbers. Got: {column_widths!r}")
    for row in rows:
        if not isinstance(row, list | tuple) or len(row) != len(columns):
            raise ReportPdfError(f"Each table row must have {len(columns)} values. Got: {row!r}")
    _render_rows(
        document,
        rows,
        headings=columns,
        col_widths=tuple(column_widths) if column_widths else None,
        first_row_as_headings=True,
        headings_style=heading_style,
        text_align="LEFT",
        line_height=5,
        borders_layout="SINGLE_TOP_LINE",
        repeat_headings=1,
    )


def _render_section(document: _ReportDocument, section: dict) -> None:
    if not isinstance(section, dict):
        raise ReportPdfError(f"Each section must be a dict. Got: {section!r}")
    heading = section.get("heading")
    if heading:
        document.ln(3)
        document.use_font(12, bold=True)
        document.multi_cell(0, 7, document.clean(str(heading)), new_x="LMARGIN", new_y="NEXT")
    document.use_font(9)
    if section.get("text") is not None:
        document.multi_cell(0, 5, _cell_text(document, section["text"]), new_x="LMARGIN", new_y="NEXT")
    rows = section.get("rows")
    columns = section.get("columns")
    if columns is not None:
        _render_table(document, list(columns), list(rows or []), section.get("column_widths"))
    elif rows:
        _render_label_value_rows(document, list(rows))


def render_report_pdf(report: dict, archived_files: list[dict], generated_at: datetime | None = None) -> bytes:
    """Return the PDF bytes for the report.

    archived_files is a list of dicts with: archive_key, original_filename, mimetype, size, sha256, uploaded_at.
    """
    if not isinstance(report, dict):
        raise ReportPdfError("report must be a dict with a title and a list of sections.")
    sections = report.get("sections") or []
    if not isinstance(sections, list):
        raise ReportPdfError("report sections must be a list.")
    generated_at = generated_at or datetime.now(UTC)
    generated_at_text = generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
    title = str(report.get("title") or "Process archive")

    document = _ReportDocument(title=title, generated_at=generated_at_text)
    document.add_page()
    document.use_font(16, bold=True)
    document.multi_cell(0, 9, document.clean(title), new_x="LMARGIN", new_y="NEXT")
    document.use_font(9)
    metadata = list(report.get("metadata") or []) + [["Archive generated", generated_at_text]]
    _render_label_value_rows(document, metadata)

    for section in sections:
        _render_section(document, section)

    file_rows = [
        [
            index,
            archived_file["original_filename"],
            archived_file.get("uploaded_at") or "-",
            format_size(archived_file["size"]),
            archived_file["sha256"],
        ]
        for index, archived_file in enumerate(archived_files, start=1)
    ]
    document.ln(3)
    document.use_font(12, bold=True)
    document.multi_cell(0, 7, document.clean("Archived files"), new_x="LMARGIN", new_y="NEXT")
    document.use_font(9)
    document.multi_cell(
        0,
        5,
        document.clean(
            "These files are stored next to this PDF in the archive. The archive file names start with the "
            "number in the first column. Use the SHA-256 value to confirm that a file was not changed."
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    document.use_font(7)
    heading_style = FontFace(emphasis="BOLD", fill_color=(230, 230, 230))
    _render_rows(
        document,
        file_rows,
        headings=["#", "File name", "Uploaded", "Size", "SHA-256"],
        empty_text="No files were uploaded.",
        col_widths=(6, 30, 18, 11, 35),
        first_row_as_headings=True,
        headings_style=heading_style,
        text_align="LEFT",
        line_height=4,
        borders_layout="SINGLE_TOP_LINE",
        repeat_headings=1,
    )

    return bytes(document.output())
