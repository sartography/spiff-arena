from flask import Flask
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.generate_markdown_table import GenerateMarkdownTable

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGenerateMarkdownTable(BaseTest):
    def setup_script_attributes_context(self) -> ScriptAttributesContext:
        return ScriptAttributesContext(
            task=None,
            environment_identifier="unit_testing",
            process_instance_id=1,
            process_model_identifier="test_process_model",
        )

    def run_generate_markdown_table_test(self, columns: list) -> None:
        data = [
            {"name": "Alice", "age": 30, "created_at": 1609459200},
            {"name": "Bob", "age": 25, "created_at": 1609545600},
        ]
        script_attributes_context = self.setup_script_attributes_context()
        result = GenerateMarkdownTable().run(
            script_attributes_context,
            columns=columns,
            data=data,
        )
        expected_result = (
            "| Name | Age | Created At |\n"
            "| ---- | ---- | ---- |\n"
            "| Alice | 30 | SPIFF_FORMAT:::convert_seconds_to_date_time_for_display(1609459200) |\n"
            "| Bob | 25 | SPIFF_FORMAT:::convert_seconds_to_date_time_for_display(1609545600) |\n"
        )
        assert result == expected_result

    def test_generate_markdown_table_script(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        columns = [
            {"property": "name", "label": "Name"},
            {"property": "age", "label": "Age"},
            {"property": "created_at", "label": "Created At", "formatter": "convert_seconds_to_date_time_for_display"},
        ]
        self.run_generate_markdown_table_test(columns)

    def test_generate_markdown_table_script_handles_vertical_bars_in_data(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        columns = [
            {"property": "name", "label": "Name"},
            {"property": "description", "label": "Description"},
        ]
        data = [
            {"name": "Alice", "description": "Alice's description | with a vertical bar"},
            {"name": "Bob", "description": "Bob's description | with another vertical bar"},
        ]
        script_attributes_context = self.setup_script_attributes_context()
        result = GenerateMarkdownTable().run(
            script_attributes_context,
            columns=columns,
            data=data,
        )
        expected_result = (
            "| Name | Description |\n"
            "| ---- | ---- |\n"
            "| Alice | Alice's description \\| with a vertical bar |\n"
            "| Bob | Bob's description \\| with another vertical bar |\n"
        )
        assert result == expected_result

    def test_generate_markdown_table_script_supports_string_columns_for_ease_of_use(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        columns = [
            "name",
            {"property": "age", "label": "Age"},
            {"property": "created_at", "label": "Created At", "formatter": "convert_seconds_to_date_time_for_display"},
        ]
        self.run_generate_markdown_table_test(columns)

    def test_generate_markdown_table_script_skips_sanitization_if_desired(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        columns = [
            {"property": "name", "label": "Name"},
            {"property": "description", "label": "Description", "sanitize": False},
        ]
        data = [
            {"name": "Alice", "description": "Alice's `description | with a vertical` bar"},
            {"name": "Bob", "description": "Bob's `description | with another vertical` bar"},
        ]
        script_attributes_context = self.setup_script_attributes_context()
        result = GenerateMarkdownTable().run(
            script_attributes_context,
            columns=columns,
            data=data,
        )
        expected_result = (
            "| Name | Description |\n"
            "| ---- | ---- |\n"
            "| Alice | Alice's `description | with a vertical` bar |\n"
            "| Bob | Bob's `description | with another vertical` bar |\n"
        )
        assert result == expected_result
