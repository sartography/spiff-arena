"""APIs for dealing with process groups, process models, and process instances."""
from contextlib import suppress

from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.routes.process_instances_controller import process_instance_start


def get_onboarding() -> Response:
    result = {}

    with suppress(Exception):
        process_instance, processor = process_instance_start("misc/jonjon/onboarding1")

        if processor is not None:
            if process_instance.status == "complete":
                workflow_data = processor.bpmn_process_instance.data
                result = workflow_data.get("onboarding", {})
            elif process_instance.status == "user_input_required" and len(process_instance.active_human_tasks) > 0:
                result = {
                    "type": "user_input_required",
                    "process_instance_id": process_instance.id,
                    "task_id": process_instance.active_human_tasks[0].task_id,
                }

    return make_response(result, 200)
