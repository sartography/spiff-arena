"""APIs for dealing with process groups, process models, and process instances."""

from flask import g
from flask import make_response
from flask.wrappers import Response
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor


def get_onboarding() -> Response:
    result: dict = {}
    persistence_level = "none"  # Going to default this to none for now as we aren't using it interactively and its
    # creating a lot of extra data in the database and UI.  We can revisit this later if we need to.
    # This is a short term fix that removes some of the potential benefits - such as routing users through an actual
    # workflow, asking questions, and saving information about them.
    # Hope to replace this with Extensions in the future.
    try:
        process_instance = ProcessInstanceModel(
            status=ProcessInstanceStatus.not_started.value,
            process_initiator_id=g.user.id,
            process_model_identifier="site-administration/onboarding",
            process_model_display_name="On Boarding",
            persistence_level=persistence_level,
        )
        processor = ProcessInstanceProcessor(process_instance)
    except ProcessEntityNotFoundError:
        # The process doesn't exist, so bail out without an error
        return make_response(result, 200)
    try:
        processor.do_engine_steps(save=False, execution_strategy_name="greedy")
        bpmn_process = processor.bpmn_process_instance
        if bpmn_process.is_completed():
            workflow_data = bpmn_process.data
            result = workflow_data.get("onboarding", {})
        task = processor.next_task()
        if task:
            result["task_id"] = task.id
            result["instructions"] = JinjaService.render_instructions_for_end_user(task)
    except WorkflowException as e:
        raise ApiError.from_workflow_exception("onboard_failed", "Error building onboarding message", e) from e
    except Exception as e:
        raise ApiError("onboard_failed", "Error building onboarding message") from e

    return make_response(result, 200)
