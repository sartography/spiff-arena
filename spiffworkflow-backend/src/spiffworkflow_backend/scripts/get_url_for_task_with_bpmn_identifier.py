from typing import Any

from flask import current_app
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor


class GetUrlForTaskWithBpmnIdentifier(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return (
            "Returns the url to the task show page for a task with the given bpmn identifier. The script task calling"
            " this MUST be in the same process as the desired task and should be next to each other in the diagram."
        )

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        bpmn_identifier = args[0]
        if bpmn_identifier is None:
            raise Exception("Bpmn identifier is required for get_url_for_task_with_bpmn_identifier")

        spiff_task = script_attributes_context.task
        if spiff_task is None:
            raise Exception("Initial spiff task not given to get_url_for_task_with_bpmn_identifier")

        desired_spiff_task = ProcessInstanceProcessor.get_task_by_bpmn_identifier(bpmn_identifier, spiff_task.workflow)
        if desired_spiff_task is None:
            raise Exception(
                f"Could not find a task with bpmn identifier '{bpmn_identifier}' in get_url_for_task_with_bpmn_identifier"
            )

        if not desired_spiff_task.task_spec.manual:
            raise Exception(
                f"Given bpmn identifier ({bpmn_identifier}) represents a task that cannot be completed by people and"
                " therefore it does not have a url to retrieve"
            )

        public = True
        public_segment = ""
        if "public" in kwargs:
            public = kwargs["public"]
        if public is True:
            public_segment = "/public"

        guid = str(desired_spiff_task.id)
        fe_url = current_app.config["SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND"]
        url = f"{fe_url}{public_segment}/tasks/{script_attributes_context.process_instance_id}/{guid}"
        return url
