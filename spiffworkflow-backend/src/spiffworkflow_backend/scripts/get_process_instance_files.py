import base64
from typing import Any
from urllib.parse import quote

from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService


class GetProcessInstanceFiles(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return (
            "Returns every file uploaded to the current process instance, oldest first, as a list of dicts with "
            "id, filename, mimetype, digest, created_at_in_seconds, and file_reference. This includes files that "
            "task data no longer references. Pass include_contents=True to also get data_url (the base64 "
            "encoded file). That is expensive, so use it only in a service task parameter or a similar "
            "short-lived value, and do not store it in task data."
        )

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        process_instance_id = script_attributes_context.process_instance_id
        if process_instance_id is None:
            raise self.get_proces_instance_id_is_missing_error("get_process_instance_files")
        include_contents = bool(kwargs.get("include_contents", args[0] if args else False))

        file_data_models = (
            ProcessInstanceFileDataModel.query.filter_by(process_instance_id=process_instance_id)
            .order_by(ProcessInstanceFileDataModel.id)
            .all()
        )

        files = []
        for file_data in file_data_models:
            encoded_filename = quote(file_data.filename, safe="")
            mime_and_name = f"data:{file_data.mimetype};name={encoded_filename};base64,"
            file_dict = {
                "id": file_data.id,
                "filename": file_data.filename,
                "mimetype": file_data.mimetype,
                "digest": file_data.digest,
                "created_at_in_seconds": file_data.created_at_in_seconds,
                "file_reference": f"{mime_and_name}{ProcessInstanceService.FILE_DATA_DIGEST_PREFIX}{file_data.digest}",
            }
            if include_contents:
                file_dict["data_url"] = mime_and_name + base64.b64encode(file_data.get_contents()).decode("ascii")
            files.append(file_dict)
        return files
