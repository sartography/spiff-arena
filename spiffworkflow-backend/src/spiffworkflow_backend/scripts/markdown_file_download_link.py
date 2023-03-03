"""Markdown_file_download_link."""
from typing import Any
from urllib.parse import unquote

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
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        # example input:
        #  "data:some/mimetype;name=testing.txt;base64,7a2051ffefd1eaf475dbef9fda019cb3d4a10eb8aea4c2c2a84a50a797a541bf"
        digest_reference = args[0]
        parts = digest_reference.split(";")
        digest = parts[2].split(",")[1]
        label = parts[1].split("=")[1]
        process_model_identifier = script_attributes_context.process_model_identifier
        modified_process_model_identifier = (
            ProcessModelInfo.modify_process_identifier_for_path_param(
                process_model_identifier
            )
        )
        process_instance_id = script_attributes_context.process_instance_id
        url = current_app.config["SPIFFWORKFLOW_BACKEND_URL"]
        url += (
            f"/v1.0/process-data-file-download/{modified_process_model_identifier}/"
            + f"{process_instance_id}/{digest}"
        )
        link = f"[{label}]({url})"

        return link
