"""APIs for dealing with process groups, process models, and process instances."""
from contextlib import suppress

from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend import db
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.routes.process_instances_controller import _process_instance_start
from spiffworkflow_backend.services.jinja_service import JinjaService


def get_onboarding() -> Response:
    result = {}

    with suppress(Exception):
        process_instance, processor = _process_instance_start("site-administration/onboarding")

        if processor is not None:
            if process_instance.status == "complete":
                workflow_data = processor.bpmn_process_instance.data
                result = workflow_data.get("onboarding", {})
            elif process_instance.status == "user_input_required" and len(process_instance.active_human_tasks) > 0:
                result = {
                    "type": "user_input_required",
                    "process_instance_id": process_instance.id,
                }

            task = processor.next_task()
            db.session.flush()
            if task:
                task_model: TaskModel | None = TaskModel.query.filter_by(
                    guid=str(task.id), process_instance_id=process_instance.id
                ).first()
                if task_model is not None:
                    result["task_id"] = task_model.guid
                    result["instructions"] = JinjaService.render_instructions_for_end_user(task_model)

    return make_response(result, 200)
