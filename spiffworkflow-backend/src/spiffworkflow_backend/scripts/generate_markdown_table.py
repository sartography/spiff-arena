from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GenerateMarkdownTable(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Given column info and data, returns a string suitable for use in markdown to show a table."""

    def generate_table_headers(self, columns: list) -> list[dict]:
        table_headers = []
        for column in columns:
            if not isinstance(column, dict):
                column_dict = {"property": column, "label": column.replace("_", " ").capitalize()}
            else:
                column_dict = column
            table_headers.append(column_dict)
        return table_headers

    def generate_table_rows(self, columns: list, data: list, table_formatters: dict[str, str]) -> str:
        table = ""
        for item in data:
            row = []
            for column in columns:
                if isinstance(column, dict):
                    property_name = column["property"]
                else:
                    property_name = column
                value = str(item.get(property_name, ""))
                if property_name in table_formatters:
                    if table_formatters[property_name] == "convert_seconds_to_date_time_for_display":
                        value = f"SPIFF_FORMAT:::convert_seconds_to_date_time_for_display({value})"
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
                        with keys 'property', 'label', and 'formatter'.
        :param data: List of dictionaries containing the data.
        :return: A string containing the markdown table.
        """
        columns: list = args[0]
        data: list = args[1]

        table_headers = self.generate_table_headers(columns)
        table_formatters = {header["property"]: header.get("formatter", "") for header in table_headers}

        header_labels = [header["label"] for header in table_headers]
        table = "| " + " | ".join(header_labels) + " |\n"
        table += "| " + " | ".join(["----"] * len(header_labels)) + " |\n"
        table += self.generate_table_rows(columns, data, table_formatters)
        return table
