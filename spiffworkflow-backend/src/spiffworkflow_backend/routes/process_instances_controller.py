"""APIs for dealing with process groups, process models, and process instances."""
import json
from typing import Any

import flask.wrappers
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.process_instance import ProcessInstanceApiSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceCannotBeDeletedError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from spiffworkflow_backend.models.process_instance_report import ProcessInstanceReportModel
from spiffworkflow_backend.models.process_instance_report import Report
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.models.spec_reference import SpecReferenceNotFoundError
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.routes.process_api_blueprint import _find_process_instance_by_id_or_raise
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.routes.process_api_blueprint import _un_modify_modified_process_model_id
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsNotEnqueuedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_report_service import ProcessInstanceReportService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.task_service import TaskService

# from spiffworkflow_backend.services.process_instance_report_service import (
#     ProcessInstanceReportFilter,
# )


def _process_instance_create(
    process_model_identifier: str,
) -> ProcessInstanceModel:
    process_model = _get_process_model(process_model_identifier)
    if process_model.primary_file_name is None:
        raise ApiError(
            error_code="process_model_missing_primary_bpmn_file",
            message=(
                f"Process Model '{process_model_identifier}' does not have a primary"
                " bpmn file. One must be set in order to instantiate this model."
            ),
            status_code=400,
        )

    process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
        process_model_identifier, g.user
    )
    return process_instance


def process_instance_create(
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    process_model_identifier = _un_modify_modified_process_model_id(modified_process_model_identifier)

    process_instance = _process_instance_create(process_model_identifier)
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=201,
        mimetype="application/json",
    )


def _process_instance_run(
    process_instance: ProcessInstanceModel,
) -> ProcessInstanceProcessor | None:
    if process_instance.status != "not_started":
        raise ApiError(
            error_code="process_instance_not_runnable",
            message=f"Process Instance ({process_instance.id}) is currently running or has already run.",
            status_code=400,
        )

    processor = None
    try:
        if not ProcessInstanceQueueService.is_enqueued_to_run_in_the_future(process_instance):
            processor = ProcessInstanceService.run_process_instance_with_processor(process_instance)
    except (
        ApiError,
        ProcessInstanceIsNotEnqueuedError,
        ProcessInstanceIsAlreadyLockedError,
    ) as e:
        ErrorHandlingService.handle_error(process_instance, e)
        raise e
    except Exception as e:
        ErrorHandlingService.handle_error(process_instance, e)
        # FIXME: this is going to point someone to the wrong task - it's misinformation for errors in sub-processes.
        # we need to recurse through all last tasks if the last task is a call activity or subprocess.
        if processor is not None:
            task = processor.bpmn_process_instance.last_task
            raise ApiError.from_task(
                error_code="unknown_exception",
                message=f"An unknown error occurred. Original error: {e}",
                status_code=400,
                task=task,
            ) from e
        raise e

    if not current_app.config["SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER_IN_CREATE_APP"]:
        MessageService.correlate_all_message_instances()

    return processor


def process_instance_run(
    modified_process_model_identifier: str,
    process_instance_id: int,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = _process_instance_run(process_instance)

    # for mypy
    if processor is not None:
        process_instance_api = ProcessInstanceService.processor_to_process_instance_api(processor)
        process_instance_data = processor.get_data()
        process_instance_metadata = ProcessInstanceApiSchema().dump(process_instance_api)
        process_instance_metadata["data"] = process_instance_data
        return Response(json.dumps(process_instance_metadata), status=200, mimetype="application/json")

    return make_response(jsonify(process_instance), 200)


def _process_instance_start(
    process_model_identifier: str,
) -> tuple[ProcessInstanceModel, ProcessInstanceProcessor | None]:
    process_instance = _process_instance_create(process_model_identifier)
    processor = _process_instance_run(process_instance)
    return process_instance, processor


def process_instance_terminate(
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)

    try:
        with ProcessInstanceQueueService.dequeued(process_instance):
            processor.terminate()
    except (
        ProcessInstanceIsNotEnqueuedError,
        ProcessInstanceIsAlreadyLockedError,
    ) as e:
        ErrorHandlingService.handle_error(process_instance, e)
        raise e

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_suspend(
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)

    try:
        with ProcessInstanceQueueService.dequeued(process_instance):
            processor.suspend()
    except (
        ProcessInstanceIsNotEnqueuedError,
        ProcessInstanceIsAlreadyLockedError,
    ) as e:
        ErrorHandlingService.handle_error(process_instance, e)
        raise e

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_resume(
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)

    try:
        with ProcessInstanceQueueService.dequeued(process_instance):
            processor.resume()
    except (
        ProcessInstanceIsNotEnqueuedError,
        ProcessInstanceIsAlreadyLockedError,
    ) as e:
        ErrorHandlingService.handle_error(process_instance, e)
        raise e

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_list_for_me(
    body: dict[str, Any],
    process_model_identifier: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    ProcessInstanceReportService.add_or_update_filter(
        body["report_metadata"]["filter_by"], {"field_name": "with_relation_to_me", "field_value": True}
    )
    return process_instance_list(
        process_model_identifier=process_model_identifier,
        page=page,
        per_page=per_page,
        body=body,
    )


def process_instance_list(
    body: dict[str, Any],
    process_model_identifier: str | None = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    response_json = ProcessInstanceReportService.run_process_instance_report(
        report_metadata=body["report_metadata"],
        page=page,
        per_page=per_page,
        user=g.user,
    )

    json_data_hash = JsonDataModel.create_and_insert_json_data_from_dict(body["report_metadata"])
    response_json["report_hash"] = json_data_hash
    db.session.commit()

    return make_response(jsonify(response_json), 200)


def process_instance_report_show(
    report_hash: str | None = None,
    report_id: int | None = None,
    report_identifier: str | None = None,
) -> flask.wrappers.Response:
    if report_hash is None and report_id is None and report_identifier is None:
        raise ApiError(
            error_code="report_key_missing",
            message=(
                "A report key is needed to lookup a report. Either choose a report_hash, report_id, or"
                " report_identifier."
            ),
        )
    response_result: Report | ProcessInstanceReportModel | None = None
    if report_hash is not None:
        json_data = JsonDataModel.query.filter_by(hash=report_hash).first()
        if json_data is None:
            raise ApiError(
                error_code="report_metadata_not_found",
                message=f"Could not find report metadata for {report_hash}.",
            )
        response_result = {
            "id": 0,
            "identifier": "custom",
            "name": "custom",
            "report_metadata": json_data.data,
        }
    else:
        response_result = ProcessInstanceReportService.report_with_identifier(g.user, report_id, report_identifier)

    return make_response(jsonify(response_result), 200)


def process_instance_report_column_list(
    process_model_identifier: str | None = None,
) -> flask.wrappers.Response:
    table_columns = ProcessInstanceReportService.builtin_column_options()
    system_report_column_options = ProcessInstanceReportService.system_report_column_options()
    columns_for_metadata_query = (
        db.session.query(ProcessInstanceMetadataModel.key)
        .order_by(ProcessInstanceMetadataModel.key)
        .distinct()  # type: ignore
    )
    if process_model_identifier:
        columns_for_metadata_query = columns_for_metadata_query.join(ProcessInstanceModel)
        columns_for_metadata_query = columns_for_metadata_query.filter(
            ProcessInstanceModel.process_model_identifier == process_model_identifier
        )

    columns_for_metadata = columns_for_metadata_query.all()
    columns_for_metadata_strings = [
        {"Header": i[0], "accessor": i[0], "filterable": True} for i in columns_for_metadata
    ]
    return make_response(jsonify(table_columns + system_report_column_options + columns_for_metadata_strings), 200)


def process_instance_show_for_me(
    modified_process_model_identifier: str,
    process_instance_id: int,
    process_identifier: str | None = None,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
    return _get_process_instance(
        process_instance=process_instance,
        modified_process_model_identifier=modified_process_model_identifier,
        process_identifier=process_identifier,
    )


def process_instance_show(
    modified_process_model_identifier: str,
    process_instance_id: int,
    process_identifier: str | None = None,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    return _get_process_instance(
        process_instance=process_instance,
        modified_process_model_identifier=modified_process_model_identifier,
        process_identifier=process_identifier,
    )


def process_instance_delete(
    process_instance_id: int, modified_process_model_identifier: str
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)

    if not process_instance.has_terminal_status():
        raise ProcessInstanceCannotBeDeletedError(
            f"Process instance ({process_instance.id}) cannot be deleted since it does"
            f" not have a terminal status. Current status is {process_instance.status}."
        )

    # (Pdb) db.session.delete
    # <bound method delete of <sqlalchemy.orm.scoping.scoped_session object at 0x103eaab30>>
    db.session.query(ProcessInstanceQueueModel).filter_by(process_instance_id=process_instance.id).delete()
    db.session.delete(process_instance)
    db.session.commit()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_report_list(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    process_instance_reports = ProcessInstanceReportModel.query.filter_by(
        created_by_id=g.user.id,
    ).all()

    return make_response(jsonify(process_instance_reports), 200)


def process_instance_report_create(body: dict[str, Any]) -> flask.wrappers.Response:
    process_instance_report = ProcessInstanceReportModel.create_report(
        identifier=body["identifier"],
        user=g.user,
        report_metadata=body["report_metadata"],
    )

    return make_response(jsonify(process_instance_report), 201)


def process_instance_report_update(
    report_id: int,
    body: dict[str, Any],
) -> flask.wrappers.Response:
    process_instance_report = ProcessInstanceReportModel.query.filter_by(
        id=report_id,
        created_by_id=g.user.id,
    ).first()
    if process_instance_report is None:
        raise ApiError(
            error_code="unknown_process_instance_report",
            message="Unknown process instance report",
            status_code=404,
        )

    process_instance_report.report_metadata = body["report_metadata"]
    db.session.commit()

    return make_response(jsonify(process_instance_report), 201)


def process_instance_report_delete(
    report_id: int,
) -> flask.wrappers.Response:
    process_instance_report = ProcessInstanceReportModel.query.filter_by(
        id=report_id,
        created_by_id=g.user.id,
    ).first()
    if process_instance_report is None:
        raise ApiError(
            error_code="unknown_process_instance_report",
            message="Unknown process instance report",
            status_code=404,
        )

    db.session.delete(process_instance_report)
    db.session.commit()

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_task_list_without_task_data_for_me(
    modified_process_model_identifier: str,
    process_instance_id: int,
    most_recent_tasks_only: bool = False,
    bpmn_process_guid: str | None = None,
    to_task_guid: str | None = None,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
    return process_instance_task_list(
        _modified_process_model_identifier=modified_process_model_identifier,
        process_instance=process_instance,
        most_recent_tasks_only=most_recent_tasks_only,
        bpmn_process_guid=bpmn_process_guid,
        to_task_guid=to_task_guid,
    )


def process_instance_task_list_without_task_data(
    modified_process_model_identifier: str,
    process_instance_id: int,
    most_recent_tasks_only: bool = False,
    bpmn_process_guid: str | None = None,
    to_task_guid: str | None = None,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    return process_instance_task_list(
        _modified_process_model_identifier=modified_process_model_identifier,
        process_instance=process_instance,
        most_recent_tasks_only=most_recent_tasks_only,
        bpmn_process_guid=bpmn_process_guid,
        to_task_guid=to_task_guid,
    )


def process_instance_task_list(
    _modified_process_model_identifier: str,
    process_instance: ProcessInstanceModel,
    bpmn_process_guid: str | None = None,
    to_task_guid: str | None = None,
    most_recent_tasks_only: bool = False,
) -> flask.wrappers.Response:
    bpmn_process_ids = []
    if bpmn_process_guid:
        bpmn_process = BpmnProcessModel.query.filter_by(guid=bpmn_process_guid).first()
        if bpmn_process is None:
            raise ApiError(
                error_code="bpmn_process_not_found",
                message=(
                    f"Cannot find a bpmn process with guid '{bpmn_process_guid}' for process instance"
                    f" '{process_instance.id}'"
                ),
                status_code=400,
            )

        bpmn_processes = TaskService.bpmn_process_and_descendants([bpmn_process])
        bpmn_process_ids = [p.id for p in bpmn_processes]

    task_model_query = db.session.query(TaskModel).filter(
        TaskModel.process_instance_id == process_instance.id, TaskModel.state.not_in(["LIKELY", "MAYBE"])  # type: ignore
    )

    to_task_model: TaskModel | None = None
    task_models_of_parent_bpmn_processes_guids: list[str] = []
    if to_task_guid is not None:
        to_task_model = TaskModel.query.filter_by(guid=to_task_guid, process_instance_id=process_instance.id).first()
        if to_task_model is None:
            raise ApiError(
                error_code="task_not_found",
                message=f"Cannot find a task with guid '{to_task_guid}' for process instance '{process_instance.id}'",
                status_code=400,
            )

        if to_task_model.state != "COMPLETED":
            # TODO: find a better term for viewing at task state
            raise ApiError(
                error_code="task_cannot_be_viewed_at",
                message=(
                    f"Desired task with guid '{to_task_guid}' for process instance '{process_instance.id}' was never"
                    " completed and therefore cannot be viewed at."
                ),
                status_code=400,
            )

        (
            _parent_bpmn_processes,
            task_models_of_parent_bpmn_processes,
        ) = TaskService.task_models_of_parent_bpmn_processes(to_task_model)
        task_models_of_parent_bpmn_processes_guids = [p.guid for p in task_models_of_parent_bpmn_processes if p.guid]
        if to_task_model.runtime_info and (
            "instance" in to_task_model.runtime_info or "iteration" in to_task_model.runtime_info
        ):
            to_task_model_parent = [to_task_model.properties_json["parent"]]
        else:
            to_task_model_parent = []
        task_model_query = task_model_query.filter(
            or_(
                TaskModel.end_in_seconds <= to_task_model.end_in_seconds,  # type: ignore
                TaskModel.guid.in_(task_models_of_parent_bpmn_processes_guids + to_task_model_parent),  # type: ignore
            )
        )

    bpmn_process_alias = aliased(BpmnProcessModel)
    direct_parent_bpmn_process_alias = aliased(BpmnProcessModel)
    direct_parent_bpmn_process_definition_alias = aliased(BpmnProcessDefinitionModel)

    task_model_query = (
        task_model_query.order_by(TaskModel.id.desc())  # type: ignore
        .join(TaskDefinitionModel, TaskDefinitionModel.id == TaskModel.task_definition_id)
        .join(bpmn_process_alias, bpmn_process_alias.id == TaskModel.bpmn_process_id)
        .outerjoin(
            direct_parent_bpmn_process_alias,
            direct_parent_bpmn_process_alias.id == bpmn_process_alias.direct_parent_process_id,
        )
        .outerjoin(
            direct_parent_bpmn_process_definition_alias,
            direct_parent_bpmn_process_definition_alias.id
            == direct_parent_bpmn_process_alias.bpmn_process_definition_id,
        )
        .join(
            BpmnProcessDefinitionModel,
            BpmnProcessDefinitionModel.id == TaskDefinitionModel.bpmn_process_definition_id,
        )
        .add_columns(
            BpmnProcessDefinitionModel.bpmn_identifier.label("bpmn_process_definition_identifier"),  # type: ignore
            BpmnProcessDefinitionModel.bpmn_name.label("bpmn_process_definition_name"),  # type: ignore
            bpmn_process_alias.guid.label("bpmn_process_guid"),
            # not sure why we needed these
            # direct_parent_bpmn_process_alias.guid.label("bpmn_process_direct_parent_guid"),
            # direct_parent_bpmn_process_definition_alias.bpmn_identifier.label(
            #     "bpmn_process_direct_parent_bpmn_identifier"
            # ),
            TaskDefinitionModel.bpmn_identifier,
            TaskDefinitionModel.bpmn_name,
            TaskDefinitionModel.typename,
            TaskDefinitionModel.properties_json.label("task_definition_properties_json"),  # type: ignore
            TaskModel.guid,
            TaskModel.state,
            TaskModel.end_in_seconds,
            TaskModel.start_in_seconds,
            TaskModel.runtime_info,
        )
    )

    if len(bpmn_process_ids) > 0:
        task_model_query = task_model_query.filter(bpmn_process_alias.id.in_(bpmn_process_ids))

    task_models = task_model_query.all()
    if most_recent_tasks_only:
        most_recent_tasks = {}
        additional_tasks = []

        # if you have a loop and there is a subprocess, and you are going around for the second time,
        # ignore the tasks in the "first loop" subprocess
        relevant_subprocess_guids = {bpmn_process_guid, None}

        bpmn_process_cache: dict[str, list[str]] = {}
        for task_model in task_models:
            if task_model.bpmn_process_guid not in bpmn_process_cache:
                bpmn_process = BpmnProcessModel.query.filter_by(guid=task_model.bpmn_process_guid).first()
                full_bpmn_process_path = TaskService.full_bpmn_process_path(bpmn_process)
                bpmn_process_cache[task_model.bpmn_process_guid] = full_bpmn_process_path
            else:
                full_bpmn_process_path = bpmn_process_cache[task_model.bpmn_process_guid]

            row_key = f"{':::'.join(full_bpmn_process_path)}:::{task_model.bpmn_identifier}"
            if row_key not in most_recent_tasks:
                most_recent_tasks[row_key] = task_model
                if task_model.typename in ["SubWorkflowTask", "CallActivity"]:
                    relevant_subprocess_guids.add(task_model.guid)
            elif task_model.runtime_info and (
                "instance" in task_model.runtime_info or "iteration" in task_model.runtime_info
            ):
                # This handles adding all instances of a MI and iterations of loop tasks
                additional_tasks.append(task_model)

        task_models = [
            task_model
            for task_model in list(most_recent_tasks.values()) + additional_tasks
            if task_model.bpmn_process_guid in relevant_subprocess_guids
        ]

    if to_task_model is not None:
        task_models_dict = json.loads(current_app.json.dumps(task_models))
        for task_model in task_models_dict:
            end_in_seconds = float(task_model["end_in_seconds"]) if task_model["end_in_seconds"] is not None else None
            if to_task_model.guid == task_model["guid"] and task_model["state"] == "COMPLETED":
                TaskService.reset_task_model_dict(task_model, state="READY")
            elif (
                end_in_seconds is None
                or to_task_model.end_in_seconds is None
                or to_task_model.end_in_seconds < end_in_seconds
            ) and task_model["guid"] in task_models_of_parent_bpmn_processes_guids:
                TaskService.reset_task_model_dict(task_model, state="WAITING")
        return make_response(jsonify(task_models_dict), 200)

    return make_response(jsonify(task_models), 200)


def process_instance_reset(
    process_instance_id: int,
    modified_process_model_identifier: str,
    to_task_guid: str,
) -> flask.wrappers.Response:
    """Reset a process instance to a particular step."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    ProcessInstanceProcessor.reset_process(process_instance, to_task_guid)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_find_by_id(
    process_instance_id: int,
) -> flask.wrappers.Response:
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
    modified_process_model_identifier = ProcessModelInfo.modify_process_identifier_for_path_param(
        process_instance.process_model_identifier
    )
    process_instance_uri = f"/process-instances/{modified_process_model_identifier}/{process_instance.id}"
    has_permission = AuthorizationService.user_has_permission(
        user=g.user,
        permission="read",
        target_uri=process_instance_uri,
    )

    uri_type = None
    if not has_permission:
        process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
        uri_type = "for-me"

    response_json = {
        "process_instance": process_instance,
        "uri_type": uri_type,
    }
    return make_response(jsonify(response_json), 200)


def send_user_signal_event(
    process_instance_id: int,
    body: dict,
) -> Response:
    """Send a user signal event to a process instance."""
    process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
    return _send_bpmn_event(process_instance, body)


def send_bpmn_event(
    modified_process_model_identifier: str,
    process_instance_id: int,
    body: dict,
) -> Response:
    """Send a bpmn event to a process instance."""
    process_instance = ProcessInstanceModel.query.filter(ProcessInstanceModel.id == int(process_instance_id)).first()
    if process_instance:
        return _send_bpmn_event(process_instance, body)
    else:
        raise ApiError(
            error_code="send_bpmn_event_error",
            message=f"Could not send event to Instance: {process_instance_id}",
        )


def _send_bpmn_event(process_instance: ProcessInstanceModel, body: dict) -> Response:
    processor = ProcessInstanceProcessor(process_instance)
    try:
        with ProcessInstanceQueueService.dequeued(process_instance):
            processor.send_bpmn_event(body)
    except (
        ProcessInstanceIsNotEnqueuedError,
        ProcessInstanceIsAlreadyLockedError,
    ) as e:
        ErrorHandlingService.handle_error(process_instance, e)
        raise e

    task = ProcessInstanceService.spiff_task_to_api_task(processor, processor.next_task())
    return make_response(jsonify(task), 200)


def _get_process_instance(
    modified_process_model_identifier: str,
    process_instance: ProcessInstanceModel,
    process_identifier: str | None = None,
) -> flask.wrappers.Response:
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    try:
        current_version_control_revision = GitService.get_current_revision()
    except GitCommandError:
        current_version_control_revision = ""

    process_model_with_diagram = None
    name_of_file_with_diagram = None
    if process_identifier:
        spec_reference = SpecReferenceCache.query.filter_by(identifier=process_identifier, type="process").first()
        if spec_reference is None:
            raise SpecReferenceNotFoundError(
                f"Could not find given process identifier in the cache: {process_identifier}"
            )

        process_model_with_diagram = ProcessModelService.get_process_model(spec_reference.process_model_id)
        name_of_file_with_diagram = spec_reference.file_name
        process_instance.process_model_with_diagram_identifier = process_model_with_diagram.id
    else:
        process_model_with_diagram = _get_process_model(process_model_identifier)
        if process_model_with_diagram.primary_file_name:
            name_of_file_with_diagram = process_model_with_diagram.primary_file_name

    if process_model_with_diagram and name_of_file_with_diagram:
        bpmn_xml_file_contents = None
        if process_instance.bpmn_version_control_identifier == current_version_control_revision:
            bpmn_xml_file_contents = SpecFileService.get_data(
                process_model_with_diagram, name_of_file_with_diagram
            ).decode("utf-8")
        else:
            try:
                bpmn_xml_file_contents = GitService.get_instance_file_contents_for_revision(
                    process_model_with_diagram,
                    process_instance.bpmn_version_control_identifier,
                    file_name=name_of_file_with_diagram,
                )
            except GitCommandError as ex:
                process_instance.bpmn_xml_file_contents_retrieval_error = str(ex)
        process_instance.bpmn_xml_file_contents = bpmn_xml_file_contents

    process_instance_as_dict = process_instance.serialized_with_metadata()
    return make_response(jsonify(process_instance_as_dict), 200)


def _find_process_instance_for_me_or_raise(
    process_instance_id: int,
) -> ProcessInstanceModel:
    process_instance: ProcessInstanceModel | None = (
        ProcessInstanceModel.query.filter_by(id=process_instance_id)
        .outerjoin(HumanTaskModel)
        .outerjoin(
            HumanTaskUserModel,
            and_(
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
                HumanTaskUserModel.user_id == g.user.id,
            ),
        )
        .filter(
            or_(
                # you were allowed to complete it
                HumanTaskUserModel.id.is_not(None),
                # or you completed it (which admins can do even if it wasn't assigned via HumanTaskUserModel)
                HumanTaskModel.completed_by_user_id == g.user.id,
                # or you started it
                ProcessInstanceModel.process_initiator_id == g.user.id,
            )
        )
        .first()
    )

    if process_instance is None:
        raise (
            ApiError(
                error_code="process_instance_cannot_be_found",
                message=f"Process instance with id {process_instance_id} cannot be found that is associated with you.",
                status_code=400,
            )
        )

    return process_instance
