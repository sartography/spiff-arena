"""APIs for dealing with process groups, process models, and process instances."""

from flask import make_response
from flask.wrappers import Response
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore

from spiffworkflow_backend import db
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.process_instances_controller import _process_instance_start
from spiffworkflow_backend.services.jinja_service import JinjaService


def get_onboarding() -> Response:
    result: dict = {}

    try:
        process_instance, processor = _process_instance_start("site-administration/onboarding")
    except ApiError:
        # The process doesn't exist, so bail out without an error
        return make_response(result, 200)
    try:
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")  # type: ignore
        if processor is not None:
            bpmn_process = processor.bpmn_process_instance
            if bpmn_process.is_completed():
                workflow_data = bpmn_process.data
                result = workflow_data.get("onboarding", {})
                # Delete the process instance, we don't need to keep this around if no users tasks were created.
                db.session.delete(process_instance)
                db.session.flush()  # Clear it out BEFORE returning.
            elif len(bpmn_process.get_ready_user_tasks()) > 0:
                process_instance.persistence_level = "full"
                processor.save()
                result = {
                    "type": "user_input_required",
                    "process_instance_id": process_instance.id,
                }
            task = processor.next_task()
            if task:
                result["task_id"] = task.id
                result["instructions"] = JinjaService.render_instructions_for_end_user(task)
    except WorkflowException as e:
        raise ApiError.from_workflow_exception("onboard_failed", "Error building onboarding message", e) from e
    except Exception as e:
        raise ApiError("onboard_failed", "Error building onboarding message") from e

    return make_response(result, 200)
