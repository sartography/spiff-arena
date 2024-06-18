from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.jinja_service import JinjaHelpers


class GenerateMarkdownTable(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Given column info and data, returns a string suitable for use in markdown to show a table."""

    def normalize_table_headers_to_dicts(self, columns: list) -> list[dict]:
        return [
            {"property": col, "label": col.replace("_", " ").capitalize()} if not isinstance(col, dict) else col
            for col in columns
        ]

    def generate_table_rows(self, table_headers: list[dict], data: list) -> str:
        table = ""
        for item in data:
            row = []
            for column in table_headers:
                property_name = column["property"]
                value = str(item.get(property_name, ""))
                if "formatter" in column and column["formatter"] == "convert_seconds_to_date_time_for_display":
                    value = f"SPIFF_FORMAT:::convert_seconds_to_date_time_for_display({value})"
                elif "sanitize" not in column or column["sanitize"] is True:
                    value = JinjaHelpers.sanitize_for_md(value)
                row.append(value)
            table += "| " + " | ".join(row) + " |\n"
        return table

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Generates a markdown table from columns and data.

        :param columns: List of column definitions. Each column can be a string or a dictionary
                        with keys 'property', 'label', 'sanitize', and 'formatter'.
        :param data: List of dictionaries containing the data.
        :return: A string containing the markdown table.
        """
        columns: list = kwargs.get("columns", args[0] if len(args) > 0 else None)
        data: list = kwargs.get("data", args[1] if len(args) > 1 else None)

        if columns is None:
            raise ValueError(
                "Missing required argument: 'columns'. Ensure that 'columns' is passed as a positional or keyword argument."
            )
        if data is None:
            raise ValueError(
                "Missing required argument: 'data'. Ensure that 'data' is passed as a positional or keyword argument."
            )
        table_headers = self.normalize_table_headers_to_dicts(columns)

        header_labels = [header["label"] for header in table_headers]
        table = "| " + " | ".join(header_labels) + " |\n"
        table += "| " + " | ".join(["----"] * len(header_labels)) + " |\n"
        table += self.generate_table_rows(table_headers, data)
        return table
