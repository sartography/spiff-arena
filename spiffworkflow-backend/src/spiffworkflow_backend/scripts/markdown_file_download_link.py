"""Markdown_file_download_link."""
from typing import Any

from flask import current_app

from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script


class GetMarkdownFileDownloadLink(Script):
    """GetMarkdownFileDownloadLink."""

    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        """Get_description."""
        return """Returns a string which is a string in markdown format."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *_args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        process_data_identifier = kwargs["key"]
        parts = kwargs["file_data"].split(";")
        file_index = kwargs["file_index"]
        label = parts[1]
        url = current_app.config["SPIFFWORKFLOW_FRONTEND_URL"]
        process_model_identifier = script_attributes_context.process_model_identifier
        modified_process_model_identifier = ProcessModelInfo.modify_process_identifier_for_path_param(process_model_identifier)
        process_instance_id = script_attributes_context.process_instance_id
        url += f"/v1.0/process-data/{modified_process_model_identifier}/{process_instance_id}/{process_data_identifier}?index={file_index}"
        link = f"[{label}]({url})"

        return link
