import flask.wrappers
from flask import jsonify
from flask import make_response
from sqlalchemy import and_

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.process_api_blueprint import _find_process_instance_by_id_or_raise


def log_list(
    modified_process_model_identifier: str,
    process_instance_id: int,
    page: int = 1,
    per_page: int = 100,
    events: bool = False,
    bpmn_name: str | None = None,
    bpmn_identifier: str | None = None,
    task_type: str | None = None,
    event_type: str | None = None,
) -> flask.wrappers.Response:
    # to make sure the process instance exists
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)

    log_query = (
        ProcessInstanceEventModel.query.filter_by(process_instance_id=process_instance.id)
        .outerjoin(TaskModel, TaskModel.guid == ProcessInstanceEventModel.task_guid)
        .outerjoin(TaskDefinitionModel, TaskDefinitionModel.id == TaskModel.task_definition_id)
        .outerjoin(
            BpmnProcessDefinitionModel,
            BpmnProcessDefinitionModel.id == TaskDefinitionModel.bpmn_process_definition_id,
        )
    )
    if not events:
        log_query = log_query.filter(
            and_(
                TaskModel.state.in_(["COMPLETED"]),  # type: ignore
                TaskDefinitionModel.typename.in_(["IntermediateThrowEvent"]),  # type: ignore
            )
        )

    if bpmn_name is not None:
        log_query = log_query.filter(TaskDefinitionModel.bpmn_name == bpmn_name)
    if bpmn_identifier is not None:
        log_query = log_query.filter(TaskDefinitionModel.bpmn_identifier == bpmn_identifier)
    if task_type is not None:
        log_query = log_query.filter(TaskDefinitionModel.typename == task_type)
    if event_type is not None:
        log_query = log_query.filter(ProcessInstanceEventModel.event_type == event_type)

    logs = (
        log_query.order_by(
            ProcessInstanceEventModel.timestamp.desc(), ProcessInstanceEventModel.id.desc()  # type: ignore
        )
        .outerjoin(UserModel, UserModel.id == ProcessInstanceEventModel.user_id)
        .add_columns(
            TaskModel.guid.label("spiff_task_guid"),  # type: ignore
            UserModel.username,
            BpmnProcessDefinitionModel.bpmn_identifier.label("bpmn_process_definition_identifier"),  # type: ignore
            BpmnProcessDefinitionModel.bpmn_name.label("bpmn_process_definition_name"),  # type: ignore
            TaskDefinitionModel.bpmn_identifier.label("task_definition_identifier"),  # type: ignore
            TaskDefinitionModel.bpmn_name.label("task_definition_name"),  # type: ignore
            TaskDefinitionModel.typename.label("bpmn_task_type"),  # type: ignore
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    response_json = {
        "results": logs.items,
        "pagination": {
            "count": len(logs.items),
            "total": logs.total,
            "pages": logs.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


def typeahead_filter_values(
    modified_process_model_identifier: str,
    process_instance_id: int,
    task_type: str | None = None,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    query = db.session.query(TaskDefinitionModel.typename).distinct()  # type: ignore
    task_types = [t.typename for t in query]
    event_types = ProcessInstanceEventType.list()
    task_definition_query = (
        db.session.query(TaskDefinitionModel.bpmn_identifier, TaskDefinitionModel.bpmn_name)
        .distinct(TaskDefinitionModel.bpmn_identifier, TaskDefinitionModel.bpmn_name)  # type: ignore
        .join(TaskModel, TaskModel.task_definition_id == TaskDefinitionModel.id)
        .join(ProcessInstanceEventModel, ProcessInstanceEventModel.task_guid == TaskModel.guid)
        .filter(TaskModel.process_instance_id == process_instance.id)
    )
    if task_type is not None:
        task_definition_query = task_definition_query.filter(TaskDefinitionModel.typename == task_type)
    task_definitions = task_definition_query.all()

    task_bpmn_names: set[str] = set()
    task_bpmn_identifiers: set[str] = set()
    for task_definition in task_definitions:
        # not checking for None so we also exclude empty strings
        if task_definition.bpmn_name:
            task_bpmn_names.add(task_definition.bpmn_name)
        task_bpmn_identifiers.add(task_definition.bpmn_identifier)

    return make_response(
        jsonify(
            {
                "task_types": task_types,
                "event_types": event_types,
                "task_bpmn_names": list(task_bpmn_names),
                "task_bpmn_identifiers": list(task_bpmn_identifiers),
            }
        ),
        200,
    )


def error_detail_show(
    modified_process_model_identifier: str,
    process_instance_id: int,
    process_instance_event_id: int,
) -> flask.wrappers.Response:
    process_instance_event = ProcessInstanceEventModel.query.filter_by(id=process_instance_event_id).first()
    if process_instance_event is None:
        raise (
            ApiError(
                error_code="process_instance_event_cannot_be_found",
                message=f"Process instance event cannot be found: {process_instance_event_id}",
                status_code=400,
            )
        )
    return make_response(jsonify(process_instance_event.error_details[0]), 200)
