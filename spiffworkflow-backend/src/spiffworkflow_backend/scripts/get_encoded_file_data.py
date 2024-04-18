import base64
from typing import Any

from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetEncodedFileData(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Returns a string which is the encoded file data. This is a very expensive call."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # example input:
        #  "data:some/mimetype;name=testing.txt;base64,spifffiledatadigest+7a2051ffefd1eaf475dbef9fda019cb3d4a10eb8aea4c2c2a84a50a797a541bf"  # noqa: B950,E501
        digest_reference = args[0]
        digest = digest_reference[-64:]
        process_instance_id = script_attributes_context.process_instance_id

        file_data = ProcessInstanceFileDataModel.query.filter_by(
            digest=digest,
            process_instance_id=process_instance_id,
        ).first()

        base64_value = base64.b64encode(file_data.get_contents()).decode("ascii")
        encoded_file_data = f"data:{file_data.mimetype};name={file_data.filename};base64,{base64_value}"

        return encoded_file_data
