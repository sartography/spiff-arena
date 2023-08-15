"""APIs for dealing with process groups, process models, and process instances."""
from contextlib import suppress

from flask import g
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_instance_processor import CustomBpmnScriptEngine
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor


def get_onboarding() -> Response:
    result = {}

    with suppress(Exception):
        process_instance = ProcessInstanceModel(
            status=ProcessInstanceStatus.not_started.value,
            process_initiator_id=g.user.id,
            process_model_identifier="site-administration/onboarding",
            process_model_display_name="Onboarding",
            persistence_level="none",
        )
        processor = ProcessInstanceProcessor(
            process_instance, script_engine=CustomBpmnScriptEngine(use_restricted_script_engine=True)
        )
        processor.do_engine_steps(save=False, execution_strategy_name="greedy")
        if processor is not None:
            bpmn_process = processor.bpmn_process_instance
            if bpmn_process.is_completed():
                workflow_data = bpmn_process.data
                result = workflow_data.get("onboarding", {})
            elif len(bpmn_process.get_ready_user_tasks()) > 0:
                result = {
                    "type": "user_input_required",
                    "process_instance_id": process_instance.id,
                }
            task = processor.next_task()
            if task:
                result["task_id"] = task.id
                result["instructions"] = JinjaService.render_instructions_for_end_user(task)

    return make_response(result, 200)
