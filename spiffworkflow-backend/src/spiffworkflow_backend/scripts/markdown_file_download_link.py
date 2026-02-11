from typing import Any

from flask import current_app

from spiffworkflow_backend.helpers.api_version import build_api_url
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class MarkdownFileDownloadLink(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Returns a string which is a string in markdown format."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # example input:
        #  "data:some/mimetype;name=testing.txt;base64,spifffiledatadigest+7a2051ffefd1eaf475dbef9fda019cb3d4a10eb8aea4c2c2a84a50a797a541bf"  # noqa: E501
        digest_reference = args[0]
        parts = digest_reference.split(";")
        digest = parts[2].split(",")[1][-64:]
        label = parts[1].split("=")[1]
        process_model_identifier = script_attributes_context.process_model_identifier
        if process_model_identifier is None:
            raise self.get_proces_model_identifier_is_missing_error("markdown_file_download_link")
        modified_process_model_identifier = ProcessModelInfo.modify_process_identifier_for_path_param(process_model_identifier)
        process_instance_id = script_attributes_context.process_instance_id
        if process_instance_id is None:
            raise self.get_proces_instance_id_is_missing_error("save_process_instance_metadata")
        backend_url = current_app.config["SPIFFWORKFLOW_BACKEND_URL"]
        api_path_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"]
        endpoint = f"process-data-file-download/{modified_process_model_identifier}/{process_instance_id}/{digest}"

        url = build_api_url(backend_url, api_path_prefix, endpoint)
        link = f"[{label}]({url})"

        return link


# Backwards compatibility class - same functionality with "Get" prefix
class GetMarkdownFileDownloadLink(MarkdownFileDownloadLink):
    pass
