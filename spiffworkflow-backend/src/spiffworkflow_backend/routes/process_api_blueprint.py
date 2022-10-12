"""APIs for dealing with process groups, process models, and process instances."""
import json
import os
import random
import string
import uuid
from typing import Any
from typing import Dict
from typing import Optional
from typing import TypedDict
from typing import Union

import connexion  # type: ignore
import flask.wrappers
import jinja2
from flask import Blueprint
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask import request
from flask.wrappers import Response
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from lxml import etree  # type: ignore
from lxml.builder import ElementMaker  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from sqlalchemy import desc

from spiffworkflow_backend.exceptions.process_entity_not_found_error import (
    ProcessEntityNotFoundError,
)
from spiffworkflow_backend.models.active_task import ActiveTaskModel
from spiffworkflow_backend.models.file import FileSchema
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.message_triggerable_process_model import (
    MessageTriggerableProcessModel,
)
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceApiSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.secret_model import SecretAllowedProcessSchema
from spiffworkflow_backend.models.secret_model import SecretModel
from spiffworkflow_backend.models.secret_model import SecretModelSchema
from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.script_unit_test_runner import ScriptUnitTestRunner
from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.service_task_service import ServiceTaskService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.user_service import UserService


class TaskDataSelectOption(TypedDict):
    """TaskDataSelectOption."""

    value: str
    label: str


class ReactJsonSchemaSelectOption(TypedDict):
    """ReactJsonSchemaSelectOption."""

    type: str
    title: str
    enum: list[str]


process_api_blueprint = Blueprint("process_api", __name__)


def status() -> flask.wrappers.Response:
    """Status."""
    ProcessInstanceModel.query.filter().first()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_group_add(
    body: Dict[str, Union[str, bool, int]]
) -> flask.wrappers.Response:
    """Add_process_group."""
    process_model_service = ProcessModelService()
    process_group = ProcessGroupSchema().load(body)
    process_model_service.add_process_group(process_group)
    return Response(
        json.dumps(ProcessGroupSchema().dump(process_group)),
        status=201,
        mimetype="application/json",
    )


def process_group_delete(process_group_id: str) -> flask.wrappers.Response:
    """Process_group_delete."""
    ProcessModelService().process_group_delete(process_group_id)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_group_update(
    process_group_id: str, body: Dict[str, Union[str, bool, int]]
) -> Dict[str, Union[str, bool, int]]:
    """Process Group Update."""
    process_group = ProcessGroupSchema().load(body)
    ProcessModelService().update_process_group(process_group)
    return ProcessGroupSchema().dump(process_group)  # type: ignore


def process_groups_list(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    """Process_groups_list."""
    process_groups = ProcessModelService().get_process_groups()
    batch = ProcessModelService().get_batch(
        items=process_groups, page=page, per_page=per_page
    )
    pages = len(process_groups) // per_page
    remainder = len(process_groups) % per_page
    if remainder > 0:
        pages += 1
    response_json = {
        "results": ProcessGroupSchema(many=True).dump(batch),
        "pagination": {
            "count": len(batch),
            "total": len(process_groups),
            "pages": pages,
        },
    }
    return Response(json.dumps(response_json), status=200, mimetype="application/json")


def process_group_show(
    process_group_id: str,
) -> Any:
    """Process_group_show."""
    try:
        process_group = ProcessModelService().get_process_group(process_group_id)
    except ProcessEntityNotFoundError as exception:
        raise (
            ApiError(
                error_code="process_group_cannot_be_found",
                message=f"Process group cannot be found: {process_group_id}",
                status_code=400,
            )
        ) from exception
    return ProcessGroupSchema().dump(process_group)


def process_model_add(
    body: Dict[str, Union[str, bool, int]]
) -> flask.wrappers.Response:
    """Add_process_model."""
    process_model_info = ProcessModelInfoSchema().load(body)
    if process_model_info is None:
        raise ApiError(
            error_code="process_model_could_not_be_created",
            message=f"Process Model could not be created from given body: {body}",
            status_code=400,
        )

    process_model_service = ProcessModelService()
    process_group = process_model_service.get_process_group(
        process_model_info.process_group_id
    )
    if process_group is None:
        raise ApiError(
            error_code="process_model_could_not_be_created",
            message=f"Process Model could not be created from given body because Process Group could not be found: {body}",
            status_code=400,
        )

    process_model_info.process_group = process_group
    process_model_service.add_spec(process_model_info)
    return Response(
        json.dumps(ProcessModelInfoSchema().dump(process_model_info)),
        status=201,
        mimetype="application/json",
    )


def process_model_delete(
    process_group_id: str, process_model_id: str
) -> flask.wrappers.Response:
    """Process_model_delete."""
    ProcessModelService().process_model_delete(process_model_id)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_model_update(
    process_group_id: str, process_model_id: str, body: Dict[str, Union[str, bool, int]]
) -> Any:
    """Process_model_update."""
    body_include_list = ["display_name", "primary_file_name", "primary_process_id"]
    body_filtered = {
        include_item: body[include_item]
        for include_item in body_include_list
        if include_item in body
    }

    process_model = get_process_model(process_model_id, process_group_id)
    ProcessModelService().update_spec(process_model, body_filtered)
    return ProcessModelInfoSchema().dump(process_model)


def process_model_show(process_group_id: str, process_model_id: str) -> Any:
    """Process_model_show."""
    process_model = get_process_model(process_model_id, process_group_id)
    files = sorted(SpecFileService.get_files(process_model))
    process_model.files = files
    process_model_json = ProcessModelInfoSchema().dump(process_model)
    return process_model_json


def process_model_list(
    process_group_identifier: Optional[str] = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Process model list!"""
    process_models = ProcessModelService().get_process_models(
        process_group_id=process_group_identifier
    )
    batch = ProcessModelService().get_batch(
        process_models, page=page, per_page=per_page
    )
    pages = len(process_models) // per_page
    remainder = len(process_models) % per_page
    if remainder > 0:
        pages += 1
    response_json = {
        "results": ProcessModelInfoSchema(many=True).dump(batch),
        "pagination": {
            "count": len(batch),
            "total": len(process_models),
            "pages": pages,
        },
    }

    return Response(json.dumps(response_json), status=200, mimetype="application/json")


def get_file(process_group_id: str, process_model_id: str, file_name: str) -> Any:
    """Get_file."""
    process_model = get_process_model(process_model_id, process_group_id)
    files = SpecFileService.get_files(process_model, file_name)
    if len(files) == 0:
        raise ApiError(
            error_code="unknown file",
            message=f"No information exists for file {file_name}"
            f" it does not exist in workflow {process_model_id}.",
            status_code=404,
        )

    file = files[0]
    file_contents = SpecFileService.get_data(process_model, file.name)
    file.file_contents = file_contents
    file.process_model_id = process_model.id
    file.process_group_id = process_model.process_group_id
    return FileSchema().dump(file)


def process_model_file_update(
    process_group_id: str, process_model_id: str, file_name: str
) -> flask.wrappers.Response:
    """Process_model_file_update."""
    process_model = get_process_model(process_model_id, process_group_id)

    request_file = get_file_from_request()
    request_file_contents = request_file.stream.read()
    if not request_file_contents:
        raise ApiError(
            error_code="file_contents_empty",
            message="Given request file does not have any content",
            status_code=400,
        )

    SpecFileService.update_file(process_model, file_name, request_file_contents)

    if current_app.config["GIT_COMMIT_ON_SAVE"]:
        git_output = GitService.commit(
            message=f"User: {g.user.username} clicked save for {process_group_id}/{process_model_id}/{file_name}"
        )
        current_app.logger.info(f"git output: {git_output}")
    else:
        current_app.logger.info("Git commit on save is disabled")

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_model_file_delete(
    process_group_id: str, process_model_id: str, file_name: str
) -> flask.wrappers.Response:
    """Process_model_file_delete."""
    process_model = get_process_model(process_model_id, process_group_id)
    try:
        SpecFileService.delete_file(process_model, file_name)
    except FileNotFoundError as exception:
        raise (
            ApiError(
                error_code="process_model_file_cannot_be_found",
                message=f"Process model file cannot be found: {file_name}",
                status_code=400,
            )
        ) from exception

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def add_file(process_group_id: str, process_model_id: str) -> flask.wrappers.Response:
    """Add_file."""
    process_model = get_process_model(process_model_id, process_group_id)
    request_file = get_file_from_request()
    if not request_file.filename:
        raise ApiError(
            error_code="could_not_get_filename",
            message="Could not get filename from request",
            status_code=400,
        )

    file = SpecFileService.add_file(
        process_model, request_file.filename, request_file.stream.read()
    )
    file_contents = SpecFileService.get_data(process_model, file.name)
    file.file_contents = file_contents
    file.process_model_id = process_model.id
    file.process_group_id = process_model.process_group_id
    return Response(
        json.dumps(FileSchema().dump(file)), status=201, mimetype="application/json"
    )


def process_instance_create(
    process_group_id: str, process_model_id: str
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_instance = ProcessInstanceService.create_process_instance(
        process_model_id, g.user, process_group_identifier=process_group_id
    )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=201,
        mimetype="application/json",
    )


def process_instance_run(
    process_group_id: str,
    process_model_id: str,
    process_instance_id: int,
    do_engine_steps: bool = True,
) -> flask.wrappers.Response:
    """Process_instance_run."""
    process_instance = ProcessInstanceService().get_process_instance(
        process_instance_id
    )
    processor = ProcessInstanceProcessor(process_instance)

    if do_engine_steps:
        try:
            processor.do_engine_steps()
        except ApiError as e:
            ErrorHandlingService().handle_error(processor, e)
            raise e
        except Exception as e:
            ErrorHandlingService().handle_error(processor, e)
            task = processor.bpmn_process_instance.last_task
            raise ApiError.from_task(
                error_code="unknown_exception",
                message=f"An unknown error occurred. Original error: {e}",
                status_code=400,
                task=task,
            ) from e
        processor.save()
        ProcessInstanceService.update_task_assignments(processor)

        if not current_app.config["PROCESS_WAITING_MESSAGES"]:
            MessageService.process_message_instances()

    process_instance_api = ProcessInstanceService.processor_to_process_instance_api(
        processor
    )
    process_instance_data = processor.get_data()
    process_instance_metadata = ProcessInstanceApiSchema().dump(process_instance_api)
    process_instance_metadata["data"] = process_instance_data
    return Response(
        json.dumps(process_instance_metadata), status=200, mimetype="application/json"
    )


def process_instance_terminate(
    process_group_id: str,
    process_model_id: str,
    process_instance_id: int,
    do_engine_steps: bool = True,
) -> flask.wrappers.Response:
    """Process_instance_run."""
    process_instance = ProcessInstanceService().get_process_instance(
        process_instance_id
    )
    processor = ProcessInstanceProcessor(process_instance)
    processor.terminate()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_log_list(
    process_group_id: str,
    process_model_id: str,
    process_instance_id: int,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    """Process_instance_log_list."""
    # to make sure the process instance exists
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)

    logs = (
        SpiffLoggingModel.query.filter(
            SpiffLoggingModel.process_instance_id == process_instance.id
        )
        .order_by(SpiffLoggingModel.timestamp.desc())  # type: ignore
        .join(
            UserModel, isouter=True
        )  # isouter since if we don't have a user, we still want the log
        .add_columns(
            UserModel.username,
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


def message_instance_list(
    process_instance_id: Optional[int] = None,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    """Message_instance_list."""
    # to make sure the process instance exists
    message_instances_query = MessageInstanceModel.query

    if process_instance_id:
        message_instances_query = message_instances_query.filter_by(
            process_instance_id=process_instance_id
        )

    message_instances = (
        message_instances_query.order_by(
            MessageInstanceModel.created_at_in_seconds.desc(),  # type: ignore
            MessageInstanceModel.id.desc(),  # type: ignore
        )
        .join(MessageModel)
        .join(ProcessInstanceModel)
        .add_columns(
            MessageModel.identifier.label("message_identifier"),
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.process_group_identifier,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    response_json = {
        "results": message_instances.items,
        "pagination": {
            "count": len(message_instances.items),
            "total": message_instances.total,
            "pages": message_instances.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


# body: {
#   payload: dict,
#   process_instance_id: Optional[int],
# }
def message_start(
    message_identifier: str,
    body: Dict[str, Any],
) -> flask.wrappers.Response:
    """Message_start."""
    message_model = MessageModel.query.filter_by(identifier=message_identifier).first()
    if message_model is None:
        raise (
            ApiError(
                error_code="unknown_message",
                message=f"Could not find message with identifier: {message_identifier}",
                status_code=404,
            )
        )

    if "payload" not in body:
        raise (
            ApiError(
                error_code="missing_payload",
                message="Body is missing payload.",
                status_code=400,
            )
        )

    process_instance = None
    if "process_instance_id" in body:
        # to make sure we have a valid process_instance_id
        process_instance = find_process_instance_by_id_or_raise(
            body["process_instance_id"]
        )

        message_instance = MessageInstanceModel.query.filter_by(
            process_instance_id=process_instance.id,
            message_model_id=message_model.id,
            message_type="receive",
            status="ready",
        ).first()
        if message_instance is None:
            raise (
                ApiError(
                    error_code="cannot_find_waiting_message",
                    message=f"Could not find waiting message for identifier {message_identifier} "
                    f"and process instance {process_instance.id}",
                    status_code=400,
                )
            )
        MessageService.process_message_receive(
            message_instance, message_model.name, body["payload"]
        )

    else:
        message_triggerable_process_model = (
            MessageTriggerableProcessModel.query.filter_by(
                message_model_id=message_model.id
            ).first()
        )

        if message_triggerable_process_model is None:
            raise (
                ApiError(
                    error_code="cannot_start_message",
                    message=f"Message with identifier cannot be start with message: {message_identifier}",
                    status_code=400,
                )
            )

        process_instance = MessageService.process_message_triggerable_process_model(
            message_triggerable_process_model,
            message_model.name,
            body["payload"],
            g.user,
        )

    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )


def process_instance_list(
    process_group_identifier: Optional[str] = None,
    process_model_identifier: Optional[str] = None,
    page: int = 1,
    per_page: int = 100,
    start_from: Optional[int] = None,
    start_till: Optional[int] = None,
    end_from: Optional[int] = None,
    end_till: Optional[int] = None,
    process_status: Optional[str] = None,
) -> flask.wrappers.Response:
    """Process_instance_list."""
    process_instance_query = ProcessInstanceModel.query
    if process_model_identifier is not None and process_group_identifier is not None:
        process_model = get_process_model(
            process_model_identifier, process_group_identifier
        )

        process_instance_query = process_instance_query.filter_by(
            process_model_identifier=process_model.id
        )

    # this can never happen. obviously the class has the columns it defines. this is just to appease mypy.
    if (
        ProcessInstanceModel.start_in_seconds is None
        or ProcessInstanceModel.end_in_seconds is None
    ):
        raise (
            ApiError(
                error_code="unexpected_condition",
                message="Something went very wrong",
                status_code=500,
            )
        )

    if start_from is not None:
        process_instance_query = process_instance_query.filter(
            ProcessInstanceModel.start_in_seconds >= start_from
        )
    if start_till is not None:
        process_instance_query = process_instance_query.filter(
            ProcessInstanceModel.start_in_seconds <= start_till
        )
    if end_from is not None:
        process_instance_query = process_instance_query.filter(
            ProcessInstanceModel.end_in_seconds >= end_from
        )
    if end_till is not None:
        process_instance_query = process_instance_query.filter(
            ProcessInstanceModel.end_in_seconds <= end_till
        )
    if process_status is not None:
        process_status_array = process_status.split(",")
        process_instance_query = process_instance_query.filter(
            ProcessInstanceModel.status.in_(process_status_array)  # type: ignore
        )

    process_instances = process_instance_query.order_by(
        ProcessInstanceModel.start_in_seconds.desc(), ProcessInstanceModel.id.desc()  # type: ignore
    ).paginate(page=page, per_page=per_page, error_out=False)

    response_json = {
        "results": process_instances.items,
        "pagination": {
            "count": len(process_instances.items),
            "total": process_instances.total,
            "pages": process_instances.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


def process_instance_show(
    process_group_id: str, process_model_id: str, process_instance_id: int
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)
    current_version_control_revision = GitService.get_current_revision()
    process_model = get_process_model(process_model_id, process_group_id)

    if process_model.primary_file_name:
        if (
            process_instance.bpmn_version_control_identifier
            == current_version_control_revision
        ):
            bpmn_xml_file_contents = SpecFileService.get_data(
                process_model, process_model.primary_file_name
            )
        else:
            bpmn_xml_file_contents = GitService.get_instance_file_contents_for_revision(
                process_model, process_instance.bpmn_version_control_identifier
            )
        process_instance.bpmn_xml_file_contents = bpmn_xml_file_contents

    return make_response(jsonify(process_instance), 200)


def process_instance_delete(
    process_group_id: str, process_model_id: str, process_instance_id: int
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)

    db.session.delete(process_instance)
    db.session.commit()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_report_list(
    process_group_id: str, process_model_id: str, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Process_instance_report_list."""
    process_model = get_process_model(process_model_id, process_group_id)

    process_instance_reports = ProcessInstanceReportModel.query.filter_by(
        process_group_identifier=process_group_id,
        process_model_identifier=process_model.id,
    ).all()

    return make_response(jsonify(process_instance_reports), 200)


def process_instance_report_create(
    process_group_id: str, process_model_id: str, body: Dict[str, Any]
) -> flask.wrappers.Response:
    """Process_instance_report_create."""
    ProcessInstanceReportModel.create_report(
        identifier=body["identifier"],
        process_group_identifier=process_group_id,
        process_model_identifier=process_model_id,
        user=g.user,
        report_metadata=body["report_metadata"],
    )

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_report_update(
    process_group_id: str,
    process_model_id: str,
    report_identifier: str,
    body: Dict[str, Any],
) -> flask.wrappers.Response:
    """Process_instance_report_create."""
    process_instance_report = ProcessInstanceReportModel.query.filter_by(
        identifier=report_identifier,
        process_group_identifier=process_group_id,
        process_model_identifier=process_model_id,
    ).first()
    if process_instance_report is None:
        raise ApiError(
            error_code="unknown_process_instance_report",
            message="Unknown process instance report",
            status_code=404,
        )

    process_instance_report.report_metadata = body["report_metadata"]
    db.session.commit()

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_report_delete(
    process_group_id: str,
    process_model_id: str,
    report_identifier: str,
) -> flask.wrappers.Response:
    """Process_instance_report_create."""
    process_instance_report = ProcessInstanceReportModel.query.filter_by(
        identifier=report_identifier,
        process_group_identifier=process_group_id,
        process_model_identifier=process_model_id,
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


def service_tasks_show() -> flask.wrappers.Response:
    """Service_tasks_show."""
    available_connectors = ServiceTaskService.available_connectors()
    print(available_connectors)

    return Response(
        json.dumps(available_connectors), status=200, mimetype="application/json"
    )


def process_instance_report_show(
    process_group_id: str,
    process_model_id: str,
    report_identifier: str,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    """Process_instance_list."""
    process_model = get_process_model(process_model_id, process_group_id)

    process_instances = (
        ProcessInstanceModel.query.filter_by(process_model_identifier=process_model.id)
        .order_by(
            ProcessInstanceModel.start_in_seconds.desc(), ProcessInstanceModel.id.desc()  # type: ignore
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    process_instance_report = ProcessInstanceReportModel.query.filter_by(
        identifier=report_identifier
    ).first()
    if process_instance_report is None:
        raise ApiError(
            error_code="unknown_process_instance_report",
            message="Unknown process instance report",
            status_code=404,
        )

    substitution_variables = request.args.to_dict()
    result_dict = process_instance_report.generate_report(
        process_instances.items, substitution_variables
    )

    # update this if we go back to a database query instead of filtering in memory
    result_dict["pagination"] = {
        "count": len(result_dict["results"]),
        "total": len(result_dict["results"]),
        "pages": 1,
    }

    return Response(json.dumps(result_dict), status=200, mimetype="application/json")


def task_list_my_tasks(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    """Task_list_my_tasks."""
    principal = find_principal_or_raise()

    active_tasks = (
        ActiveTaskModel.query.filter_by(assigned_principal_id=principal.id)
        .order_by(desc(ActiveTaskModel.id))  # type: ignore
        .join(ProcessInstanceModel)
        # just need this add_columns to add the process_model_identifier. Then add everything back that was removed.
        .add_columns(
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.process_group_identifier,
            ActiveTaskModel.task_data,
            ActiveTaskModel.task_name,
            ActiveTaskModel.task_title,
            ActiveTaskModel.task_type,
            ActiveTaskModel.task_status,
            ActiveTaskModel.task_id,
            ActiveTaskModel.id,
            ActiveTaskModel.process_model_display_name,
            ActiveTaskModel.process_instance_id,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    tasks = [ActiveTaskModel.to_task(active_task) for active_task in active_tasks.items]

    response_json = {
        "results": tasks,
        "pagination": {
            "count": len(active_tasks.items),
            "total": active_tasks.total,
            "pages": active_tasks.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


def process_instance_task_list(
    process_instance_id: int, all_tasks: bool = False
) -> flask.wrappers.Response:
    """Process_instance_task_list."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)

    spiff_tasks = None
    if all_tasks:
        spiff_tasks = processor.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
    else:
        spiff_tasks = processor.get_all_user_tasks()

    tasks = []
    for spiff_task in spiff_tasks:
        task = ProcessInstanceService.spiff_task_to_api_task(spiff_task)
        task.data = spiff_task.data
        tasks.append(task)

    return make_response(jsonify(tasks), 200)


def task_show(process_instance_id: int, task_id: str) -> flask.wrappers.Response:
    """Task_show."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)
    process_model = get_process_model(
        process_instance.process_model_identifier,
        process_instance.process_group_identifier,
    )

    form_schema_file_name = ""
    form_ui_schema_file_name = ""
    spiff_task = get_spiff_task_from_process_instance(task_id, process_instance)
    extensions = spiff_task.task_spec.extensions

    if "properties" in extensions:
        properties = extensions["properties"]
        if "formJsonSchemaFilename" in properties:
            form_schema_file_name = properties["formJsonSchemaFilename"]
        if "formUiSchemaFilename" in properties:
            form_ui_schema_file_name = properties["formUiSchemaFilename"]
    task = ProcessInstanceService.spiff_task_to_api_task(spiff_task)
    task.data = spiff_task.data
    task.process_model_display_name = process_model.display_name

    process_model_with_form = process_model
    all_processes = SpecFileService.get_all_bpmn_process_identifiers_for_process_model(
        process_model
    )
    if task.process_name not in all_processes:
        bpmn_file_full_path = (
            ProcessInstanceProcessor.bpmn_file_full_path_from_bpmn_process_identifier(
                task.process_name
            )
        )
        relative_path = os.path.relpath(
            bpmn_file_full_path, start=FileSystemService.root_path()
        )
        process_model_relative_path = os.path.dirname(relative_path)
        process_model_with_form = (
            ProcessModelService.get_process_model_from_relative_path(
                process_model_relative_path
            )
        )

    if task.type == "User Task":
        if not form_schema_file_name:
            raise (
                ApiError(
                    error_code="missing_form_file",
                    message=f"Cannot find a form file for process_instance_id: {process_instance_id}, task_id: {task_id}",
                    status_code=400,
                )
            )

        form_contents = prepare_form_data(
            form_schema_file_name,
            task.data,
            process_model_with_form,
        )

        try:
            # form_contents is a str
            form_dict = json.loads(form_contents)
        except Exception as exception:
            raise (
                ApiError(
                    error_code="error_loading_form",
                    message=f"Could not load form schema from: {form_schema_file_name}. Error was: {str(exception)}",
                    status_code=400,
                )
            ) from exception

        if task.data:
            _update_form_schema_with_task_data_as_needed(form_dict, task.data)

        if form_contents:
            task.form_schema = form_dict

        if form_ui_schema_file_name:
            ui_form_contents = prepare_form_data(
                form_ui_schema_file_name,
                task.data,
                process_model_with_form,
            )
            if ui_form_contents:
                task.form_ui_schema = ui_form_contents
    elif task.type == "Manual Task":
        if task.properties and task.data:
            if task.properties["instructionsForEndUser"]:
                task.properties["instructionsForEndUser"] = render_jinja_template(
                    task.properties["instructionsForEndUser"], task.data
                )
    return make_response(jsonify(task), 200)


def task_submit(
    process_instance_id: int,
    task_id: str,
    body: Dict[str, Any],
    terminate_loop: bool = False,
) -> flask.wrappers.Response:
    """Task_submit_user_data."""
    principal = find_principal_or_raise()
    active_task_assigned_to_me = find_active_task_by_id_or_raise(
        process_instance_id, task_id, principal.id
    )

    process_instance = find_process_instance_by_id_or_raise(
        active_task_assigned_to_me.process_instance_id
    )

    processor = ProcessInstanceProcessor(process_instance)
    spiff_task = get_spiff_task_from_process_instance(
        task_id, process_instance, processor=processor
    )

    if spiff_task.state != TaskState.READY:
        raise (
            ApiError(
                error_code="invalid_state",
                message="You may not update a task unless it is in the READY state.",
                status_code=400,
            )
        )

    if terminate_loop and spiff_task.is_looping():
        spiff_task.terminate_loop()

    # TODO: support repeating fields
    # Extract the details specific to the form submitted
    # form_data = WorkflowService().extract_form_data(body, spiff_task)

    ProcessInstanceService.complete_form_task(processor, spiff_task, body, g.user)

    # If we need to update all tasks, then get the next ready task and if it a multi-instance with the same
    # task spec, complete that form as well.
    # if update_all:
    #     last_index = spiff_task.task_info()["mi_index"]
    #     next_task = processor.next_task()
    #     while next_task and next_task.task_info()["mi_index"] > last_index:
    #         __update_task(processor, next_task, form_data, user)
    #         last_index = next_task.task_info()["mi_index"]
    #         next_task = processor.next_task()

    ProcessInstanceService.update_task_assignments(processor)

    next_active_task_assigned_to_me = ActiveTaskModel.query.filter_by(
        assigned_principal_id=principal.id, process_instance_id=process_instance.id
    ).first()
    if next_active_task_assigned_to_me:
        return make_response(
            jsonify(ActiveTaskModel.to_task(next_active_task_assigned_to_me)), 200
        )

    return Response(json.dumps({"ok": True}), status=202, mimetype="application/json")


def script_unit_test_create(
    process_group_id: str, process_model_id: str, body: Dict[str, Union[str, bool, int]]
) -> flask.wrappers.Response:
    """Script_unit_test_run."""
    bpmn_task_identifier = _get_required_parameter_or_raise(
        "bpmn_task_identifier", body
    )
    input_json = _get_required_parameter_or_raise("input_json", body)
    expected_output_json = _get_required_parameter_or_raise(
        "expected_output_json", body
    )

    process_model = get_process_model(process_model_id, process_group_id)
    file = SpecFileService.get_files(process_model, process_model.primary_file_name)[0]
    if file is None:
        raise ApiError(
            error_code="cannot_find_file",
            message=f"Could not find the primary bpmn file for process_model: {process_model.id}",
            status_code=404,
        )

    # TODO: move this to an xml service or something
    file_contents = SpecFileService.get_data(process_model, file.name)
    bpmn_etree_element = SpecFileService.get_etree_element_from_binary_data(
        file_contents, file.name
    )

    nsmap = bpmn_etree_element.nsmap
    spiff_element_maker = ElementMaker(
        namespace="http://spiffworkflow.org/bpmn/schema/1.0/core", nsmap=nsmap
    )

    script_task_elements = bpmn_etree_element.xpath(
        f"//bpmn:scriptTask[@id='{bpmn_task_identifier}']",
        namespaces={"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
    )
    if len(script_task_elements) == 0:
        raise ApiError(
            error_code="missing_script_task",
            message=f"Cannot find a script task with id: {bpmn_task_identifier}",
            status_code=404,
        )
    script_task_element = script_task_elements[0]

    extension_elements = None
    extension_elements_array = script_task_element.xpath(
        "//bpmn:extensionElements",
        namespaces={"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
    )
    if len(extension_elements_array) == 0:
        bpmn_element_maker = ElementMaker(
            namespace="http://www.omg.org/spec/BPMN/20100524/MODEL", nsmap=nsmap
        )
        extension_elements = bpmn_element_maker("extensionElements")
        script_task_element.append(extension_elements)
    else:
        extension_elements = extension_elements_array[0]

    unit_test_elements = None
    unit_test_elements_array = extension_elements.xpath(
        "//spiffworkflow:unitTests",
        namespaces={"spiffworkflow": "http://spiffworkflow.org/bpmn/schema/1.0/core"},
    )
    if len(unit_test_elements_array) == 0:
        unit_test_elements = spiff_element_maker("unitTests")
        extension_elements.append(unit_test_elements)
    else:
        unit_test_elements = unit_test_elements_array[0]

    fuzz = "".join(
        random.choice(string.ascii_uppercase + string.digits)  # noqa: S311
        for _ in range(7)
    )
    unit_test_id = f"unit_test_{fuzz}"

    input_json_element = spiff_element_maker("inputJson", json.dumps(input_json))
    expected_output_json_element = spiff_element_maker(
        "expectedOutputJson", json.dumps(expected_output_json)
    )
    unit_test_element = spiff_element_maker("unitTest", id=unit_test_id)
    unit_test_element.append(input_json_element)
    unit_test_element.append(expected_output_json_element)
    unit_test_elements.append(unit_test_element)
    SpecFileService.update_file(
        process_model, file.name, etree.tostring(bpmn_etree_element)
    )

    return Response(json.dumps({"ok": True}), status=202, mimetype="application/json")


def script_unit_test_run(
    process_group_id: str, process_model_id: str, body: Dict[str, Union[str, bool, int]]
) -> flask.wrappers.Response:
    """Script_unit_test_run."""
    # FIXME: We should probably clear this somewhere else but this works
    current_app.config["THREAD_LOCAL_DATA"].process_instance_id = None

    python_script = _get_required_parameter_or_raise("python_script", body)
    input_json = _get_required_parameter_or_raise("input_json", body)
    expected_output_json = _get_required_parameter_or_raise(
        "expected_output_json", body
    )

    result = ScriptUnitTestRunner.run_with_script_and_pre_post_contexts(
        python_script, input_json, expected_output_json
    )
    return make_response(jsonify(result), 200)


def get_file_from_request() -> Any:
    """Get_file_from_request."""
    request_file = connexion.request.files.get("file")
    if not request_file:
        raise ApiError(
            error_code="no_file_given",
            message="Given request does not contain a file",
            status_code=400,
        )
    return request_file


def get_process_model(process_model_id: str, process_group_id: str) -> ProcessModelInfo:
    """Get_process_model."""
    process_model = None
    try:
        process_model = ProcessModelService().get_process_model(
            process_model_id, group_id=process_group_id
        )
    except ProcessEntityNotFoundError as exception:
        raise (
            ApiError(
                error_code="process_model_cannot_be_found",
                message=f"Process model cannot be found: {process_model_id}",
                status_code=400,
            )
        ) from exception

    return process_model


def find_principal_or_raise() -> PrincipalModel:
    """Find_principal_or_raise."""
    principal = PrincipalModel.query.filter_by(user_id=g.user.id).first()
    if principal is None:
        raise (
            ApiError(
                error_code="principal_not_found",
                message=f"Principal not found from user id: {g.user.id}",
                status_code=400,
            )
        )
    return principal  # type: ignore


def find_active_task_by_id_or_raise(
    process_instance_id: int, task_id: str, principal_id: PrincipalModel
) -> ActiveTaskModel:
    """Find_active_task_by_id_or_raise."""
    active_task_assigned_to_me = ActiveTaskModel.query.filter_by(
        process_instance_id=process_instance_id,
        task_id=task_id,
        assigned_principal_id=principal_id,
    ).first()
    if active_task_assigned_to_me is None:
        message = (
            f"Task not found for principal user {principal_id} "
            f"process_instance_id: {process_instance_id}, task_id: {task_id}"
        )
        raise (
            ApiError(
                error_code="task_not_found",
                message=message,
                status_code=400,
            )
        )
    return active_task_assigned_to_me  # type: ignore


def find_process_instance_by_id_or_raise(
    process_instance_id: int,
) -> ProcessInstanceModel:
    """Find_process_instance_by_id_or_raise."""
    process_instance = ProcessInstanceModel.query.filter_by(
        id=process_instance_id
    ).first()
    if process_instance is None:
        raise (
            ApiError(
                error_code="process_instance_cannot_be_found",
                message=f"Process instance cannot be found: {process_instance_id}",
                status_code=400,
            )
        )
    return process_instance  # type: ignore


def get_value_from_array_with_index(array: list, index: int) -> Any:
    """Get_value_from_array_with_index."""
    if index < 0:
        return None

    if index >= len(array):
        return None

    return array[index]


def prepare_form_data(
    form_file: str, task_data: Union[dict, None], process_model: ProcessModelInfo
) -> str:
    """Prepare_form_data."""
    if task_data is None:
        return ""

    file_contents = SpecFileService.get_data(process_model, form_file).decode("utf-8")
    return render_jinja_template(file_contents, task_data)


def render_jinja_template(unprocessed_template: str, data: dict[str, Any]) -> str:
    """Render_jinja_template."""
    jinja_environment = jinja2.Environment(
        autoescape=True, lstrip_blocks=True, trim_blocks=True
    )
    template = jinja_environment.from_string(unprocessed_template)
    return template.render(**data)


def get_spiff_task_from_process_instance(
    task_id: str,
    process_instance: ProcessInstanceModel,
    processor: Union[ProcessInstanceProcessor, None] = None,
) -> SpiffTask:
    """Get_spiff_task_from_process_instance."""
    if processor is None:
        processor = ProcessInstanceProcessor(process_instance)
    task_uuid = uuid.UUID(task_id)
    spiff_task = processor.bpmn_process_instance.get_task(task_uuid)

    if spiff_task is None:
        raise (
            ApiError(
                error_code="empty_task",
                message="Processor failed to obtain task.",
                status_code=500,
            )
        )
    return spiff_task


#
# Methods for secrets CRUD - maybe move somewhere else:
#
def get_secret(key: str) -> Optional[str]:
    """Get_secret."""
    return SecretService.get_secret(key)


def secret_list(
    page: int = 1,
    per_page: int = 100,
) -> Response:
    """Secret_list."""
    secrets = (
        SecretModel.query.order_by(SecretModel.key)
        .join(UserModel)
        .add_columns(
            UserModel.username,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    response_json = {
        "results": secrets.items,
        "pagination": {
            "count": len(secrets.items),
            "total": secrets.total,
            "pages": secrets.pages,
        },
    }
    return make_response(jsonify(response_json), 200)


def add_secret(body: Dict) -> Response:
    """Add secret."""
    secret_model = SecretService().add_secret(body["key"], body["value"], g.user.id)
    assert secret_model  # noqa: S101
    return Response(
        json.dumps(SecretModelSchema().dump(secret_model)),
        status=201,
        mimetype="application/json",
    )


def update_secret(key: str, body: dict) -> Response:
    """Update secret."""
    SecretService().update_secret(key, body["value"], body["creator_user_id"])
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def delete_secret(key: str) -> Response:
    """Delete secret."""
    current_user = UserService.current_user()
    SecretService.delete_secret(key, current_user.id)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def add_allowed_process_path(body: dict) -> Response:
    """Get allowed process paths."""
    allowed_process_path = SecretService.add_allowed_process(
        body["secret_id"], g.user.id, body["allowed_relative_path"]
    )
    return Response(
        json.dumps(SecretAllowedProcessSchema().dump(allowed_process_path)),
        status=201,
        mimetype="application/json",
    )


def delete_allowed_process_path(allowed_process_path_id: int) -> Response:
    """Get allowed process paths."""
    SecretService().delete_allowed_process(allowed_process_path_id, g.user.id)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def _get_required_parameter_or_raise(parameter: str, post_body: dict[str, Any]) -> Any:
    """Get_required_parameter_or_raise."""
    return_value = None
    if parameter in post_body:
        return_value = post_body[parameter]

    if return_value is None or return_value == "":
        raise (
            ApiError(
                error_code="missing_required_parameter",
                message=f"Parameter is missing from json request body: {parameter}",
                status_code=400,
            )
        )

    return return_value


# originally from: https://bitcoden.com/answers/python-nested-dictionary-update-value-where-any-nested-key-matches
def _update_form_schema_with_task_data_as_needed(
    in_dict: dict, task_data: dict
) -> None:
    """Update_nested."""
    for k, value in in_dict.items():
        if "anyOf" == k:
            # value will look like the array on the right of "anyOf": ["options_from_task_data_var:awesome_options"]
            if isinstance(value, list):
                if len(value) == 1:
                    first_element_in_value_list = value[0]
                    if isinstance(first_element_in_value_list, str):
                        if first_element_in_value_list.startswith(
                            "options_from_task_data_var:"
                        ):
                            task_data_var = first_element_in_value_list.replace(
                                "options_from_task_data_var:", ""
                            )

                            if task_data_var not in task_data:
                                raise (
                                    ApiError(
                                        error_code="missing_task_data_var",
                                        message=f"Task data is missing variable: {task_data_var}",
                                        status_code=500,
                                    )
                                )

                            select_options_from_task_data = task_data.get(task_data_var)
                            if isinstance(select_options_from_task_data, list):
                                if all(
                                    "value" in d and "label" in d
                                    for d in select_options_from_task_data
                                ):

                                    def map_function(
                                        task_data_select_option: TaskDataSelectOption,
                                    ) -> ReactJsonSchemaSelectOption:
                                        """Map_function."""
                                        return {
                                            "type": "string",
                                            "enum": [task_data_select_option["value"]],
                                            "title": task_data_select_option["label"],
                                        }

                                    options_for_react_json_schema_form = list(
                                        map(map_function, select_options_from_task_data)
                                    )

                                    in_dict[k] = options_for_react_json_schema_form
        elif isinstance(value, dict):
            _update_form_schema_with_task_data_as_needed(value, task_data)
        elif isinstance(value, list):
            for o in value:
                if isinstance(o, dict):
                    _update_form_schema_with_task_data_as_needed(o, task_data)
