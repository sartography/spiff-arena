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

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Generates a markdown table from columns and data.

        :param columns: List of column definitions. Each column can be a string or a dictionary with keys 'property', 'label', and 'formatter'.
        :param data: List of dictionaries containing the data.
        :return: A string containing the markdown table.
        """
        columns: list = args[0]
        data: list = args[1]

        table_headers = []
        table_formatters = {}
        for column in columns:
            if isinstance(column, dict):
                table_headers.append(column.get("label", column["property"]))
                if "formatter" in column:
                    table_formatters[column["property"]] = column["formatter"]
            else:
                table_headers.append(column.replace("_", " ").capitalize())

        table = "| " + " | ".join(table_headers) + " |\n"
        table += "| " + " | ".join(["----"] * len(table_headers)) + " |\n"

        for item in data:
            row = []
            for column in columns:
                property_name = column["property"] if isinstance(column, dict) else column
                value = str(item[property_name])
                if property_name in table_formatters:
                    if table_formatters[property_name] == "convert_seconds_to_date_time_for_display":
                        value = f"SPIFF_FORMAT:::convert_seconds_to_date_time_for_display({value})"
                row.append(value)
            table += "| " + " | ".join(row) + " |\n"
        return table
