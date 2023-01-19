"""Save process instance metadata."""
from typing import Any

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance_metadata import (
    ProcessInstanceMetadataModel,
)
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script


class SaveProcessInstanceMetadata(Script):
    """SaveProcessInstanceMetadata."""

    def get_description(self) -> str:
        """Get_description."""
        return """Save a given dict as process instance metadata (useful for creating reports)."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        metadata_dict = args[0]
        for key, value in metadata_dict.items():
            pim = ProcessInstanceMetadataModel.query.filter_by(
                process_instance_id=script_attributes_context.process_instance_id,
                key=key,
            ).first()
            if pim is None:
                pim = ProcessInstanceMetadataModel(
                    process_instance_id=script_attributes_context.process_instance_id,
                    key=key,
                )
            pim.value = value
            db.session.add(pim)
            db.session.commit()
