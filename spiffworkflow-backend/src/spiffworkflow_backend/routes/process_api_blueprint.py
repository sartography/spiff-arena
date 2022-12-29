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
import werkzeug
from flask import Blueprint
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import request
from flask.wrappers import Response
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from lxml import etree  # type: ignore
from lxml.builder import ElementMaker  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from sqlalchemy import and_
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import or_

from spiffworkflow_backend.exceptions.process_entity_not_found_error import (
    ProcessEntityNotFoundError,
)
from spiffworkflow_backend.models.file import FileSchema
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.message_correlation import MessageCorrelationModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.message_triggerable_process_model import (
    MessageTriggerableProcessModel,
)
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceApiSchema
from spiffworkflow_backend.models.process_instance import (
    ProcessInstanceCannotBeDeletedError,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance import (
    ProcessInstanceTaskDataCannotBeUpdatedError,
)
from spiffworkflow_backend.models.process_instance_metadata import (
    ProcessInstanceMetadataModel,
)
from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.secret_model import SecretModel
from spiffworkflow_backend.models.secret_model import SecretModelSchema
from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.models.spec_reference import SpecReferenceNotFoundError
from spiffworkflow_backend.models.spec_reference import SpecReferenceSchema
from spiffworkflow_backend.models.spiff_logging import SpiffLoggingModel
from spiffworkflow_backend.models.spiff_step_details import SpiffStepDetailsModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.user import verify_token
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_report_service import (
    ProcessInstanceReportFilter,
)
from spiffworkflow_backend.services.process_instance_report_service import (
    ProcessInstanceReportService,
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


def permissions_check(body: Dict[str, Dict[str, list[str]]]) -> flask.wrappers.Response:
    """Permissions_check."""
    if "requests_to_check" not in body:
        raise (
            ApiError(
                error_code="could_not_requests_to_check",
                message="The key 'requests_to_check' not found at root of request body.",
                status_code=400,
            )
        )
    response_dict: dict[str, dict[str, bool]] = {}
    requests_to_check = body["requests_to_check"]

    for target_uri, http_methods in requests_to_check.items():
        if target_uri not in response_dict:
            response_dict[target_uri] = {}

        for http_method in http_methods:
            permission_string = AuthorizationService.get_permission_from_http_method(
                http_method
            )
            if permission_string:
                has_permission = AuthorizationService.user_has_permission(
                    user=g.user,
                    permission=permission_string,
                    target_uri=target_uri,
                )
                response_dict[target_uri][http_method] = has_permission

    return make_response(jsonify({"results": response_dict}), 200)


def un_modify_modified_process_model_id(modified_process_model_identifier: str) -> str:
    """Un_modify_modified_process_model_id."""
    return modified_process_model_identifier.replace(":", "/")


def process_group_create(body: dict) -> flask.wrappers.Response:
    """Add_process_group."""
    process_group = ProcessGroup(**body)
    ProcessModelService.add_process_group(process_group)
    _commit_and_push_to_git(
        f"User: {g.user.username} added process group {process_group.id}"
    )
    return make_response(jsonify(process_group), 201)


def process_group_delete(modified_process_group_id: str) -> flask.wrappers.Response:
    """Process_group_delete."""
    process_group_id = un_modify_modified_process_model_id(modified_process_group_id)
    ProcessModelService().process_group_delete(process_group_id)
    _commit_and_push_to_git(
        f"User: {g.user.username} deleted process group {process_group_id}"
    )
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_group_update(
    modified_process_group_id: str, body: dict
) -> flask.wrappers.Response:
    """Process Group Update."""
    body_include_list = ["display_name", "description"]
    body_filtered = {
        include_item: body[include_item]
        for include_item in body_include_list
        if include_item in body
    }

    process_group_id = un_modify_modified_process_model_id(modified_process_group_id)
    process_group = ProcessGroup(id=process_group_id, **body_filtered)
    ProcessModelService.update_process_group(process_group)
    _commit_and_push_to_git(
        f"User: {g.user.username} updated process group {process_group_id}"
    )
    return make_response(jsonify(process_group), 200)


def process_group_list(
    process_group_identifier: Optional[str] = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Process_group_list."""
    if process_group_identifier is not None:
        process_groups = ProcessModelService.get_process_groups(
            process_group_identifier
        )
    else:
        process_groups = ProcessModelService.get_process_groups()
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
    modified_process_group_id: str,
) -> Any:
    """Process_group_show."""
    process_group_id = un_modify_modified_process_model_id(modified_process_group_id)
    try:
        process_group = ProcessModelService.get_process_group(process_group_id)
    except ProcessEntityNotFoundError as exception:
        raise (
            ApiError(
                error_code="process_group_cannot_be_found",
                message=f"Process group cannot be found: {process_group_id}",
                status_code=400,
            )
        ) from exception

    process_group.parent_groups = ProcessModelService.get_parent_group_array(
        process_group.id
    )
    return make_response(jsonify(process_group), 200)


def process_group_move(
    modified_process_group_identifier: str, new_location: str
) -> flask.wrappers.Response:
    """Process_group_move."""
    original_process_group_id = un_modify_modified_process_model_id(
        modified_process_group_identifier
    )
    new_process_group = ProcessModelService().process_group_move(
        original_process_group_id, new_location
    )
    _commit_and_push_to_git(
        f"User: {g.user.username} moved process group {original_process_group_id} to {new_process_group.id}"
    )
    return make_response(jsonify(new_process_group), 200)


def process_model_create(
    modified_process_group_id: str, body: Dict[str, Union[str, bool, int]]
) -> flask.wrappers.Response:
    """Process_model_create."""
    body_include_list = [
        "id",
        "display_name",
        "primary_file_name",
        "primary_process_id",
        "description",
        "metadata_extraction_paths",
    ]
    body_filtered = {
        include_item: body[include_item]
        for include_item in body_include_list
        if include_item in body
    }

    if modified_process_group_id is None:
        raise ApiError(
            error_code="process_group_id_not_specified",
            message="Process Model could not be created when process_group_id path param is unspecified",
            status_code=400,
        )

    unmodified_process_group_id = un_modify_modified_process_model_id(
        modified_process_group_id
    )
    process_group = ProcessModelService.get_process_group(unmodified_process_group_id)
    if process_group is None:
        raise ApiError(
            error_code="process_model_could_not_be_created",
            message=f"Process Model could not be created from given body because Process Group could not be found: {body}",
            status_code=400,
        )

    process_model_info = ProcessModelInfo(**body_filtered)  # type: ignore
    if process_model_info is None:
        raise ApiError(
            error_code="process_model_could_not_be_created",
            message=f"Process Model could not be created from given body: {body}",
            status_code=400,
        )

    ProcessModelService.add_process_model(process_model_info)
    _commit_and_push_to_git(
        f"User: {g.user.username} created process model {process_model_info.id}"
    )
    return Response(
        json.dumps(ProcessModelInfoSchema().dump(process_model_info)),
        status=201,
        mimetype="application/json",
    )


def process_model_delete(
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_model_delete."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    ProcessModelService().process_model_delete(process_model_identifier)
    _commit_and_push_to_git(
        f"User: {g.user.username} deleted process model {process_model_identifier}"
    )
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_model_update(
    modified_process_model_identifier: str, body: Dict[str, Union[str, bool, int]]
) -> Any:
    """Process_model_update."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    body_include_list = [
        "display_name",
        "primary_file_name",
        "primary_process_id",
        "description",
        "metadata_extraction_paths",
    ]
    body_filtered = {
        include_item: body[include_item]
        for include_item in body_include_list
        if include_item in body
    }

    process_model = get_process_model(process_model_identifier)
    ProcessModelService.update_process_model(process_model, body_filtered)
    _commit_and_push_to_git(
        f"User: {g.user.username} updated process model {process_model_identifier}"
    )
    return ProcessModelInfoSchema().dump(process_model)


def process_model_show(modified_process_model_identifier: str) -> Any:
    """Process_model_show."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = get_process_model(process_model_identifier)
    files = sorted(
        SpecFileService.get_files(process_model),
        key=lambda f: "" if f.name == process_model.primary_file_name else f.sort_index,
    )
    process_model.files = files
    for file in process_model.files:
        file.references = SpecFileService.get_references_for_file(file, process_model)

    process_model.parent_groups = ProcessModelService.get_parent_group_array(
        process_model.id
    )
    return make_response(jsonify(process_model), 200)


def process_model_move(
    modified_process_model_identifier: str, new_location: str
) -> flask.wrappers.Response:
    """Process_model_move."""
    original_process_model_id = un_modify_modified_process_model_id(
        modified_process_model_identifier
    )
    new_process_model = ProcessModelService().process_model_move(
        original_process_model_id, new_location
    )
    _commit_and_push_to_git(
        f"User: {g.user.username} moved process model {original_process_model_id} to {new_process_model.id}"
    )
    return make_response(jsonify(new_process_model), 200)


def process_model_publish(
    modified_process_model_identifier: str, branch_to_update: Optional[str] = None
) -> flask.wrappers.Response:
    """Process_model_publish."""
    if branch_to_update is None:
        branch_to_update = current_app.config["GIT_BRANCH_TO_PUBLISH_TO"]
    process_model_identifier = un_modify_modified_process_model_id(
        modified_process_model_identifier
    )
    pr_url = GitService().publish(process_model_identifier, branch_to_update)
    data = {"ok": True, "pr_url": pr_url}
    return Response(json.dumps(data), status=200, mimetype="application/json")


def process_model_list(
    process_group_identifier: Optional[str] = None,
    recursive: Optional[bool] = False,
    filter_runnable_by_user: Optional[bool] = False,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    """Process model list!"""
    process_models = ProcessModelService.get_process_models(
        process_group_id=process_group_identifier,
        recursive=recursive,
        filter_runnable_by_user=filter_runnable_by_user,
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


def process_list() -> Any:
    """Returns a list of all known processes.

    This includes processes that are not the
    primary process - helpful for finding possible call activities.
    """
    references = SpecReferenceCache.query.filter_by(type="process").all()
    return SpecReferenceSchema(many=True).dump(references)


def get_file(modified_process_model_identifier: str, file_name: str) -> Any:
    """Get_file."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = get_process_model(process_model_identifier)
    files = SpecFileService.get_files(process_model, file_name)
    if len(files) == 0:
        raise ApiError(
            error_code="unknown file",
            message=f"No information exists for file {file_name}"
            f" it does not exist in workflow {process_model_identifier}.",
            status_code=404,
        )

    file = files[0]
    file_contents = SpecFileService.get_data(process_model, file.name)
    file.file_contents = file_contents
    file.process_model_id = process_model.id
    # file.process_group_id = process_model.process_group_id
    return FileSchema().dump(file)


def process_model_file_update(
    modified_process_model_identifier: str, file_name: str
) -> flask.wrappers.Response:
    """Process_model_file_update."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = get_process_model(process_model_identifier)

    request_file = get_file_from_request()
    request_file_contents = request_file.stream.read()
    if not request_file_contents:
        raise ApiError(
            error_code="file_contents_empty",
            message="Given request file does not have any content",
            status_code=400,
        )

    SpecFileService.update_file(process_model, file_name, request_file_contents)
    _commit_and_push_to_git(
        f"User: {g.user.username} clicked save for {process_model_identifier}/{file_name}"
    )

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_model_file_delete(
    modified_process_model_identifier: str, file_name: str
) -> flask.wrappers.Response:
    """Process_model_file_delete."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = get_process_model(process_model_identifier)
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

    _commit_and_push_to_git(
        f"User: {g.user.username} deleted process model file {process_model_identifier}/{file_name}"
    )
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def add_file(modified_process_model_identifier: str) -> flask.wrappers.Response:
    """Add_file."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = get_process_model(process_model_identifier)
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
    _commit_and_push_to_git(
        f"User: {g.user.username} added process model file {process_model_identifier}/{file.name}"
    )
    return Response(
        json.dumps(FileSchema().dump(file)), status=201, mimetype="application/json"
    )


def process_instance_create(
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_model_identifier = un_modify_modified_process_model_id(
        modified_process_model_identifier
    )
    process_instance = (
        ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model_identifier, g.user
        )
    )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=201,
        mimetype="application/json",
    )


def process_instance_run(
    modified_process_model_identifier: str,
    process_instance_id: int,
    do_engine_steps: bool = True,
) -> flask.wrappers.Response:
    """Process_instance_run."""
    process_instance = ProcessInstanceService().get_process_instance(
        process_instance_id
    )
    if process_instance.status != "not_started":
        raise ApiError(
            error_code="process_instance_not_runnable",
            message=f"Process Instance ({process_instance.id}) is currently running or has already run.",
            status_code=400,
        )

    processor = ProcessInstanceProcessor(process_instance)

    if do_engine_steps:
        try:
            processor.do_engine_steps(save=True)
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

        if not current_app.config["RUN_BACKGROUND_SCHEDULER"]:
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
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_instance_run."""
    process_instance = ProcessInstanceService().get_process_instance(
        process_instance_id
    )
    processor = ProcessInstanceProcessor(process_instance)
    processor.terminate()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_suspend(
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_instance_suspend."""
    process_instance = ProcessInstanceService().get_process_instance(
        process_instance_id
    )
    processor = ProcessInstanceProcessor(process_instance)
    processor.suspend()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_resume(
    process_instance_id: int,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_instance_resume."""
    process_instance = ProcessInstanceService().get_process_instance(
        process_instance_id
    )
    processor = ProcessInstanceProcessor(process_instance)
    processor.resume()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_log_list(
    modified_process_model_identifier: str,
    process_instance_id: int,
    page: int = 1,
    per_page: int = 100,
    detailed: bool = False,
) -> flask.wrappers.Response:
    """Process_instance_log_list."""
    # to make sure the process instance exists
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)

    log_query = SpiffLoggingModel.query.filter(
        SpiffLoggingModel.process_instance_id == process_instance.id
    )
    if not detailed:
        log_query = log_query.filter(SpiffLoggingModel.message.in_(["State change to COMPLETED"]))  # type: ignore

    logs = (
        log_query.order_by(SpiffLoggingModel.timestamp.desc())  # type: ignore
        .join(
            UserModel, UserModel.id == SpiffLoggingModel.current_user_id, isouter=True
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
        .join(MessageModel, MessageModel.id == MessageInstanceModel.message_model_id)
        .join(ProcessInstanceModel)
        .add_columns(
            MessageModel.identifier.label("message_identifier"),
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.process_model_display_name,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    for message_instance in message_instances:
        message_correlations: dict = {}
        for (
            mcmi
        ) in (
            message_instance.MessageInstanceModel.message_correlations_message_instances
        ):
            mc = MessageCorrelationModel.query.filter_by(
                id=mcmi.message_correlation_id
            ).all()
            for m in mc:
                if m.name not in message_correlations:
                    message_correlations[m.name] = {}
                message_correlations[m.name][
                    m.message_correlation_property.identifier
                ] = m.value
        message_instance.MessageInstanceModel.message_correlations = (
            message_correlations
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


def process_instance_list_for_me(
    process_model_identifier: Optional[str] = None,
    page: int = 1,
    per_page: int = 100,
    start_from: Optional[int] = None,
    start_to: Optional[int] = None,
    end_from: Optional[int] = None,
    end_to: Optional[int] = None,
    process_status: Optional[str] = None,
    user_filter: Optional[bool] = False,
    report_identifier: Optional[str] = None,
    report_id: Optional[int] = None,
    user_group_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Process_instance_list_for_me."""
    return process_instance_list(
        process_model_identifier=process_model_identifier,
        page=page,
        per_page=per_page,
        start_from=start_from,
        start_to=start_to,
        end_from=end_from,
        end_to=end_to,
        process_status=process_status,
        user_filter=user_filter,
        report_identifier=report_identifier,
        report_id=report_id,
        user_group_identifier=user_group_identifier,
        with_relation_to_me=True,
    )


def process_instance_list(
    process_model_identifier: Optional[str] = None,
    page: int = 1,
    per_page: int = 100,
    start_from: Optional[int] = None,
    start_to: Optional[int] = None,
    end_from: Optional[int] = None,
    end_to: Optional[int] = None,
    process_status: Optional[str] = None,
    with_relation_to_me: Optional[bool] = None,
    user_filter: Optional[bool] = False,
    report_identifier: Optional[str] = None,
    report_id: Optional[int] = None,
    user_group_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Process_instance_list."""
    process_instance_report = ProcessInstanceReportService.report_with_identifier(
        g.user, report_id, report_identifier
    )

    if user_filter:
        report_filter = ProcessInstanceReportFilter(
            process_model_identifier=process_model_identifier,
            user_group_identifier=user_group_identifier,
            start_from=start_from,
            start_to=start_to,
            end_from=end_from,
            end_to=end_to,
            with_relation_to_me=with_relation_to_me,
            process_status=process_status.split(",") if process_status else None,
        )
    else:
        report_filter = (
            ProcessInstanceReportService.filter_from_metadata_with_overrides(
                process_instance_report=process_instance_report,
                process_model_identifier=process_model_identifier,
                user_group_identifier=user_group_identifier,
                start_from=start_from,
                start_to=start_to,
                end_from=end_from,
                end_to=end_to,
                process_status=process_status,
                with_relation_to_me=with_relation_to_me,
            )
        )

    response_json = ProcessInstanceReportService.run_process_instance_report(
        report_filter=report_filter,
        process_instance_report=process_instance_report,
        page=page,
        per_page=per_page,
        user=g.user,
    )

    return make_response(jsonify(response_json), 200)


def process_instance_report_column_list() -> flask.wrappers.Response:
    """Process_instance_report_column_list."""
    table_columns = ProcessInstanceReportService.builtin_column_options()
    columns_for_metadata = (
        db.session.query(ProcessInstanceMetadataModel.key)
        .order_by(ProcessInstanceMetadataModel.key)
        .distinct()  # type: ignore
        .all()
    )
    columns_for_metadata_strings = [
        {"Header": i[0], "accessor": i[0], "filterable": True}
        for i in columns_for_metadata
    ]
    return make_response(jsonify(table_columns + columns_for_metadata_strings), 200)


def process_instance_show_for_me(
    modified_process_model_identifier: str,
    process_instance_id: int,
    process_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Process_instance_show_for_me."""
    process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
    return _get_process_instance(
        process_instance=process_instance,
        modified_process_model_identifier=modified_process_model_identifier,
        process_identifier=process_identifier,
    )


def process_instance_show(
    modified_process_model_identifier: str,
    process_instance_id: int,
    process_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)
    return _get_process_instance(
        process_instance=process_instance,
        modified_process_model_identifier=modified_process_model_identifier,
        process_identifier=process_identifier,
    )


def _get_process_instance(
    modified_process_model_identifier: str,
    process_instance: ProcessInstanceModel,
    process_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """_get_process_instance."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    current_version_control_revision = GitService.get_current_revision()

    process_model_with_diagram = None
    name_of_file_with_diagram = None
    if process_identifier:
        spec_reference = SpecReferenceCache.query.filter_by(
            identifier=process_identifier
        ).first()
        if spec_reference is None:
            raise SpecReferenceNotFoundError(
                f"Could not find given process identifier in the cache: {process_identifier}"
            )

        process_model_with_diagram = ProcessModelService.get_process_model(
            spec_reference.process_model_id
        )
        name_of_file_with_diagram = spec_reference.file_name
    else:
        process_model_with_diagram = get_process_model(process_model_identifier)
        if process_model_with_diagram.primary_file_name:
            name_of_file_with_diagram = process_model_with_diagram.primary_file_name

    if process_model_with_diagram and name_of_file_with_diagram:
        if (
            process_instance.bpmn_version_control_identifier
            == current_version_control_revision
        ):
            bpmn_xml_file_contents = SpecFileService.get_data(
                process_model_with_diagram, name_of_file_with_diagram
            ).decode("utf-8")
        else:
            bpmn_xml_file_contents = GitService.get_instance_file_contents_for_revision(
                process_model_with_diagram,
                process_instance.bpmn_version_control_identifier,
                file_name=name_of_file_with_diagram,
            )
        process_instance.bpmn_xml_file_contents = bpmn_xml_file_contents

    return make_response(jsonify(process_instance), 200)


def process_instance_delete(
    process_instance_id: int, modified_process_model_identifier: str
) -> flask.wrappers.Response:
    """Create_process_instance."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)

    if not process_instance.has_terminal_status():
        raise ProcessInstanceCannotBeDeletedError(
            f"Process instance ({process_instance.id}) cannot be deleted since it does not have a terminal status. "
            f"Current status is {process_instance.status}."
        )

    # (Pdb) db.session.delete
    # <bound method delete of <sqlalchemy.orm.scoping.scoped_session object at 0x103eaab30>>
    db.session.query(SpiffLoggingModel).filter_by(
        process_instance_id=process_instance.id
    ).delete()
    db.session.query(SpiffStepDetailsModel).filter_by(
        process_instance_id=process_instance.id
    ).delete()
    db.session.delete(process_instance)
    db.session.commit()
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_instance_report_list(
    page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Process_instance_report_list."""
    process_instance_reports = ProcessInstanceReportModel.query.filter_by(
        created_by_id=g.user.id,
    ).all()

    return make_response(jsonify(process_instance_reports), 200)


def process_instance_report_create(body: Dict[str, Any]) -> flask.wrappers.Response:
    """Process_instance_report_create."""
    process_instance_report = ProcessInstanceReportModel.create_report(
        identifier=body["identifier"],
        user=g.user,
        report_metadata=body["report_metadata"],
    )

    return make_response(jsonify(process_instance_report), 201)


def process_instance_report_update(
    report_id: int,
    body: Dict[str, Any],
) -> flask.wrappers.Response:
    """Process_instance_report_create."""
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
    """Process_instance_report_create."""
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


def service_task_list() -> flask.wrappers.Response:
    """Service_task_list."""
    available_connectors = ServiceTaskService.available_connectors()
    return Response(
        json.dumps(available_connectors), status=200, mimetype="application/json"
    )


def authentication_list() -> flask.wrappers.Response:
    """Authentication_list."""
    available_authentications = ServiceTaskService.authentication_list()
    response_json = {
        "results": available_authentications,
        "connector_proxy_base_url": current_app.config["CONNECTOR_PROXY_URL"],
        "redirect_url": f"{current_app.config['SPIFFWORKFLOW_BACKEND_URL']}/v1.0/authentication_callback",
    }

    return Response(json.dumps(response_json), status=200, mimetype="application/json")


def authentication_callback(
    service: str,
    auth_method: str,
) -> werkzeug.wrappers.Response:
    """Authentication_callback."""
    verify_token(request.args.get("token"), force_run=True)
    response = request.args["response"]
    SecretService().update_secret(
        f"{service}/{auth_method}", response, g.user.id, create_if_not_exists=True
    )
    return redirect(
        f"{current_app.config['SPIFFWORKFLOW_FRONTEND_URL']}/admin/configuration"
    )


def process_instance_report_show(
    report_id: int,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    """Process_instance_report_show."""
    process_instances = ProcessInstanceModel.query.order_by(
        ProcessInstanceModel.start_in_seconds.desc(), ProcessInstanceModel.id.desc()  # type: ignore
    ).paginate(page=page, per_page=per_page, error_out=False)

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


# TODO: see comment for before_request
# @process_api_blueprint.route("/v1.0/tasks", methods=["GET"])
def task_list_my_tasks(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    """Task_list_my_tasks."""
    principal = find_principal_or_raise()
    human_tasks = (
        HumanTaskModel.query.order_by(desc(HumanTaskModel.id))  # type: ignore
        .join(ProcessInstanceModel)
        .join(HumanTaskUserModel)
        .filter_by(user_id=principal.user_id)
        .filter(HumanTaskModel.completed == False)  # noqa: E712
        # just need this add_columns to add the process_model_identifier. Then add everything back that was removed.
        .add_columns(
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.process_model_display_name,
            ProcessInstanceModel.status,
            HumanTaskModel.task_name,
            HumanTaskModel.task_title,
            HumanTaskModel.task_type,
            HumanTaskModel.task_status,
            HumanTaskModel.task_id,
            HumanTaskModel.id,
            HumanTaskModel.process_model_display_name,
            HumanTaskModel.process_instance_id,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    tasks = [HumanTaskModel.to_task(human_task) for human_task in human_tasks.items]

    response_json = {
        "results": tasks,
        "pagination": {
            "count": len(human_tasks.items),
            "total": human_tasks.total,
            "pages": human_tasks.pages,
        },
    }

    return make_response(jsonify(response_json), 200)


def task_list_for_my_open_processes(
    page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Task_list_for_my_open_processes."""
    return get_tasks(page=page, per_page=per_page)


def task_list_for_me(page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    """Task_list_for_me."""
    return get_tasks(
        processes_started_by_user=False,
        has_lane_assignment_id=False,
        page=page,
        per_page=per_page,
    )


def task_list_for_my_groups(
    user_group_identifier: Optional[str] = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Task_list_for_my_groups."""
    return get_tasks(
        user_group_identifier=user_group_identifier,
        processes_started_by_user=False,
        page=page,
        per_page=per_page,
    )


def user_group_list_for_current_user() -> flask.wrappers.Response:
    """User_group_list_for_current_user."""
    groups = g.user.groups
    # TODO: filter out the default group and have a way to know what is the default group
    group_identifiers = [i.identifier for i in groups if i.identifier != "everybody"]
    return make_response(jsonify(sorted(group_identifiers)), 200)


def get_tasks(
    processes_started_by_user: bool = True,
    has_lane_assignment_id: bool = True,
    page: int = 1,
    per_page: int = 100,
    user_group_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """Get_tasks."""
    user_id = g.user.id

    # use distinct to ensure we only get one row per human task otherwise
    # we can get back multiple for the same human task row which throws off
    # pagination later on
    # https://stackoverflow.com/q/34582014/6090676
    human_tasks_query = (
        HumanTaskModel.query.distinct()
        .outerjoin(GroupModel, GroupModel.id == HumanTaskModel.lane_assignment_id)
        .join(ProcessInstanceModel)
        .join(UserModel, UserModel.id == ProcessInstanceModel.process_initiator_id)
        .filter(HumanTaskModel.completed == False)  # noqa: E712
    )

    if processes_started_by_user:
        human_tasks_query = human_tasks_query.filter(
            ProcessInstanceModel.process_initiator_id == user_id
        ).outerjoin(
            HumanTaskUserModel,
            and_(
                HumanTaskUserModel.user_id == user_id,
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
            ),
        )
    else:
        human_tasks_query = human_tasks_query.filter(
            ProcessInstanceModel.process_initiator_id != user_id
        ).join(
            HumanTaskUserModel,
            and_(
                HumanTaskUserModel.user_id == user_id,
                HumanTaskModel.id == HumanTaskUserModel.human_task_id,
            ),
        )
        if has_lane_assignment_id:
            if user_group_identifier:
                human_tasks_query = human_tasks_query.filter(
                    GroupModel.identifier == user_group_identifier
                )
            else:
                human_tasks_query = human_tasks_query.filter(
                    HumanTaskModel.lane_assignment_id.is_not(None)  # type: ignore
                )
        else:
            human_tasks_query = human_tasks_query.filter(HumanTaskModel.lane_assignment_id.is_(None))  # type: ignore

    human_tasks = (
        human_tasks_query.add_columns(
            ProcessInstanceModel.process_model_identifier,
            ProcessInstanceModel.status.label("process_instance_status"),  # type: ignore
            ProcessInstanceModel.updated_at_in_seconds,
            ProcessInstanceModel.created_at_in_seconds,
            UserModel.username,
            GroupModel.identifier.label("user_group_identifier"),
            HumanTaskModel.task_name,
            HumanTaskModel.task_title,
            HumanTaskModel.process_model_display_name,
            HumanTaskModel.process_instance_id,
            HumanTaskUserModel.user_id.label("current_user_is_potential_owner"),
        )
        .order_by(desc(HumanTaskModel.id))  # type: ignore
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    response_json = {
        "results": human_tasks.items,
        "pagination": {
            "count": len(human_tasks.items),
            "total": human_tasks.total,
            "pages": human_tasks.pages,
        },
    }
    return make_response(jsonify(response_json), 200)


def process_instance_task_list_without_task_data_for_me(
    modified_process_model_identifier: str,
    process_instance_id: int,
    all_tasks: bool = False,
    spiff_step: int = 0,
) -> flask.wrappers.Response:
    """Process_instance_task_list_without_task_data_for_me."""
    process_instance = _find_process_instance_for_me_or_raise(process_instance_id)
    return process_instance_task_list(
        modified_process_model_identifier,
        process_instance,
        all_tasks,
        spiff_step,
        get_task_data=False,
    )


def process_instance_task_list_without_task_data(
    modified_process_model_identifier: str,
    process_instance_id: int,
    all_tasks: bool = False,
    spiff_step: int = 0,
) -> flask.wrappers.Response:
    """Process_instance_task_list_without_task_data."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)
    return process_instance_task_list(
        modified_process_model_identifier,
        process_instance,
        all_tasks,
        spiff_step,
        get_task_data=False,
    )


def process_instance_task_list_with_task_data(
    modified_process_model_identifier: str,
    process_instance_id: int,
    all_tasks: bool = False,
    spiff_step: int = 0,
) -> flask.wrappers.Response:
    """Process_instance_task_list_with_task_data."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)
    return process_instance_task_list(
        modified_process_model_identifier,
        process_instance,
        all_tasks,
        spiff_step,
        get_task_data=True,
    )


def process_instance_task_list(
    _modified_process_model_identifier: str,
    process_instance: ProcessInstanceModel,
    all_tasks: bool = False,
    spiff_step: int = 0,
    get_task_data: bool = False,
) -> flask.wrappers.Response:
    """Process_instance_task_list."""
    if spiff_step > 0:
        step_detail = (
            db.session.query(SpiffStepDetailsModel)
            .filter(
                SpiffStepDetailsModel.process_instance_id == process_instance.id,
                SpiffStepDetailsModel.spiff_step == spiff_step,
            )
            .first()
        )
        if step_detail is not None and process_instance.bpmn_json is not None:
            bpmn_json = json.loads(process_instance.bpmn_json)
            bpmn_json["tasks"] = step_detail.task_json["tasks"]
            bpmn_json["subprocesses"] = step_detail.task_json["subprocesses"]
            process_instance.bpmn_json = json.dumps(bpmn_json)

    processor = ProcessInstanceProcessor(process_instance)

    spiff_tasks = None
    if all_tasks:
        spiff_tasks = processor.bpmn_process_instance.get_tasks(TaskState.ANY_MASK)
    else:
        spiff_tasks = processor.get_all_user_tasks()

    tasks = []
    for spiff_task in spiff_tasks:
        task = ProcessInstanceService.spiff_task_to_api_task(processor, spiff_task)
        if get_task_data:
            task.data = spiff_task.data
        tasks.append(task)

    return make_response(jsonify(tasks), 200)


def task_show(process_instance_id: int, task_id: str) -> flask.wrappers.Response:
    """Task_show."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)

    if process_instance.status == ProcessInstanceStatus.suspended.value:
        raise ApiError(
            error_code="error_suspended",
            message="The process instance is suspended",
            status_code=400,
        )

    process_model = get_process_model(
        process_instance.process_model_identifier,
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

    processor = ProcessInstanceProcessor(process_instance)
    task = ProcessInstanceService.spiff_task_to_api_task(processor, spiff_task)
    task.data = spiff_task.data
    task.process_model_display_name = process_model.display_name
    task.process_model_identifier = process_model.id

    process_model_with_form = process_model
    refs = SpecFileService.get_references_for_process(process_model_with_form)
    all_processes = [i.identifier for i in refs]
    if task.process_identifier not in all_processes:
        bpmn_file_full_path = (
            ProcessInstanceProcessor.bpmn_file_full_path_from_bpmn_process_identifier(
                task.process_identifier
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

    if task.properties and task.data and "instructionsForEndUser" in task.properties:
        if task.properties["instructionsForEndUser"]:
            task.properties["instructionsForEndUser"] = render_jinja_template(
                task.properties["instructionsForEndUser"], task.data
            )
    return make_response(jsonify(task), 200)


def process_data_show(
    process_instance_id: int,
    process_data_identifier: str,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_data_show."""
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)
    processor = ProcessInstanceProcessor(process_instance)
    all_process_data = processor.get_data()
    process_data_value = None
    if process_data_identifier in all_process_data:
        process_data_value = all_process_data[process_data_identifier]

    return make_response(
        jsonify(
            {
                "process_data_identifier": process_data_identifier,
                "process_data_value": process_data_value,
            }
        ),
        200,
    )


def task_submit(
    process_instance_id: int,
    task_id: str,
    body: Dict[str, Any],
    terminate_loop: bool = False,
) -> flask.wrappers.Response:
    """Task_submit_user_data."""
    principal = find_principal_or_raise()
    process_instance = find_process_instance_by_id_or_raise(process_instance_id)
    if not process_instance.can_submit_task():
        raise ApiError(
            error_code="process_instance_not_runnable",
            message=f"Process Instance ({process_instance.id}) has status "
            f"{process_instance.status} which does not allow tasks to be submitted.",
            status_code=400,
        )

    processor = ProcessInstanceProcessor(process_instance)
    spiff_task = get_spiff_task_from_process_instance(
        task_id, process_instance, processor=processor
    )
    AuthorizationService.assert_user_can_complete_spiff_task(
        process_instance.id, spiff_task, principal.user
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

    human_task = HumanTaskModel.query.filter_by(
        process_instance_id=process_instance_id, task_id=task_id, completed=False
    ).first()
    if human_task is None:
        raise (
            ApiError(
                error_code="no_human_task",
                message="Cannot find an human task with task id '{task_id}' for process instance {process_instance_id}.",
                status_code=500,
            )
        )

    ProcessInstanceService.complete_form_task(
        processor=processor,
        spiff_task=spiff_task,
        data=body,
        user=g.user,
        human_task=human_task,
    )

    # If we need to update all tasks, then get the next ready task and if it a multi-instance with the same
    # task spec, complete that form as well.
    # if update_all:
    #     last_index = spiff_task.task_info()["mi_index"]
    #     next_task = processor.next_task()
    #     while next_task and next_task.task_info()["mi_index"] > last_index:
    #         __update_task(processor, next_task, form_data, user)
    #         last_index = next_task.task_info()["mi_index"]
    #         next_task = processor.next_task()

    next_human_task_assigned_to_me = (
        HumanTaskModel.query.filter_by(
            process_instance_id=process_instance_id, completed=False
        )
        .order_by(asc(HumanTaskModel.id))  # type: ignore
        .join(HumanTaskUserModel)
        .filter_by(user_id=principal.user_id)
        .first()
    )
    if next_human_task_assigned_to_me:
        return make_response(
            jsonify(HumanTaskModel.to_task(next_human_task_assigned_to_me)), 200
        )

    return Response(json.dumps({"ok": True}), status=202, mimetype="application/json")


def script_unit_test_create(
    modified_process_model_identifier: str, body: Dict[str, Union[str, bool, int]]
) -> flask.wrappers.Response:
    """Script_unit_test_create."""
    bpmn_task_identifier = _get_required_parameter_or_raise(
        "bpmn_task_identifier", body
    )
    input_json = _get_required_parameter_or_raise("input_json", body)
    expected_output_json = _get_required_parameter_or_raise(
        "expected_output_json", body
    )

    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = get_process_model(process_model_identifier)
    file = SpecFileService.get_files(process_model, process_model.primary_file_name)[0]
    if file is None:
        raise ApiError(
            error_code="cannot_find_file",
            message=f"Could not find the primary bpmn file for process_model: {process_model.id}",
            status_code=404,
        )

    # TODO: move this to an xml service or something
    file_contents = SpecFileService.get_data(process_model, file.name)
    bpmn_etree_element = etree.fromstring(file_contents)

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
        ".//bpmn:extensionElements",
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
    modified_process_model_identifier: str, body: Dict[str, Union[str, bool, int]]
) -> flask.wrappers.Response:
    """Script_unit_test_run."""
    # FIXME: We should probably clear this somewhere else but this works
    current_app.config["THREAD_LOCAL_DATA"].process_instance_id = None
    current_app.config["THREAD_LOCAL_DATA"].spiff_step = None

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


# process_model_id uses forward slashes on all OSes
# this seems to return an object where process_model.id has backslashes on windows
def get_process_model(process_model_id: str) -> ProcessModelInfo:
    """Get_process_model."""
    process_model = None
    try:
        process_model = ProcessModelService.get_process_model(process_model_id)
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


def find_process_instance_by_id_or_raise(
    process_instance_id: int,
) -> ProcessInstanceModel:
    """Find_process_instance_by_id_or_raise."""
    process_instance_query = ProcessInstanceModel.query.filter_by(
        id=process_instance_id
    )

    # we had a frustrating session trying to do joins and access columns from two tables. here's some notes for our future selves:
    # this returns an object that allows you to do: process_instance.UserModel.username
    # process_instance = db.session.query(ProcessInstanceModel, UserModel).filter_by(id=process_instance_id).first()
    # you can also use splat with add_columns, but it still didn't ultimately give us access to the process instance
    # attributes or username like we wanted:
    # process_instance_query.join(UserModel).add_columns(*ProcessInstanceModel.__table__.columns, UserModel.username)

    process_instance = process_instance_query.first()
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


# sample body:
# {"ref": "refs/heads/main", "repository": {"name": "sample-process-models",
# "full_name": "sartography/sample-process-models", "private": False .... }}
# test with: ngrok http 7000
# where 7000 is the port the app is running on locally
def github_webhook_receive(body: Dict) -> Response:
    """Github_webhook_receive."""
    auth_header = request.headers.get("X-Hub-Signature-256")
    AuthorizationService.verify_sha256_token(auth_header)
    result = GitService.handle_web_hook(body)
    return Response(
        json.dumps({"git_pull": result}), status=200, mimetype="application/json"
    )


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


def secret_create(body: Dict) -> Response:
    """Add secret."""
    secret_model = SecretService().add_secret(body["key"], body["value"], g.user.id)
    return Response(
        json.dumps(SecretModelSchema().dump(secret_model)),
        status=201,
        mimetype="application/json",
    )


def secret_update(key: str, body: dict) -> Response:
    """Update secret."""
    SecretService().update_secret(key, body["value"], g.user.id)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def secret_delete(key: str) -> Response:
    """Delete secret."""
    current_user = UserService.current_user()
    SecretService.delete_secret(key, current_user.id)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def task_data_update(
    process_instance_id: str,
    modified_process_model_identifier: str,
    task_id: str,
    body: Dict,
) -> Response:
    """Update task data."""
    process_instance = ProcessInstanceModel.query.filter(
        ProcessInstanceModel.id == int(process_instance_id)
    ).first()
    if process_instance:
        if process_instance.status != "suspended":
            raise ProcessInstanceTaskDataCannotBeUpdatedError(
                f"The process instance needs to be suspended to udpate the task-data. It is currently: {process_instance.status}"
            )

        process_instance_bpmn_json_dict = json.loads(process_instance.bpmn_json)
        if "new_task_data" in body:
            new_task_data_str: str = body["new_task_data"]
            new_task_data_dict = json.loads(new_task_data_str)
            if task_id in process_instance_bpmn_json_dict["tasks"]:
                process_instance_bpmn_json_dict["tasks"][task_id][
                    "data"
                ] = new_task_data_dict
                process_instance.bpmn_json = json.dumps(process_instance_bpmn_json_dict)
                db.session.add(process_instance)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    raise ApiError(
                        error_code="update_task_data_error",
                        message=f"Could not update the Instance. Original error is {e}",
                    ) from e
            else:
                raise ApiError(
                    error_code="update_task_data_error",
                    message=f"Could not find Task: {task_id} in Instance: {process_instance_id}.",
                )
    else:
        raise ApiError(
            error_code="update_task_data_error",
            message=f"Could not update task data for Instance: {process_instance_id}, and Task: {task_id}.",
        )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )


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


def update_task_data(
    process_instance_id: str,
    modified_process_model_identifier: str,
    task_id: str,
    body: Dict,
) -> Response:
    """Update task data."""
    process_instance = ProcessInstanceModel.query.filter(
        ProcessInstanceModel.id == int(process_instance_id)
    ).first()
    if process_instance:
        if process_instance.status != "suspended":
            raise ProcessInstanceTaskDataCannotBeUpdatedError(
                f"The process instance needs to be suspended to udpate the task-data. It is currently: {process_instance.status}"
            )

        process_instance_bpmn_json_dict = json.loads(process_instance.bpmn_json)
        if "new_task_data" in body:
            new_task_data_str: str = body["new_task_data"]
            new_task_data_dict = json.loads(new_task_data_str)
            if task_id in process_instance_bpmn_json_dict["tasks"]:
                process_instance_bpmn_json_dict["tasks"][task_id][
                    "data"
                ] = new_task_data_dict
                process_instance.bpmn_json = json.dumps(process_instance_bpmn_json_dict)
                db.session.add(process_instance)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    raise ApiError(
                        error_code="update_task_data_error",
                        message=f"Could not update the Instance. Original error is {e}",
                    ) from e
            else:
                raise ApiError(
                    error_code="update_task_data_error",
                    message=f"Could not find Task: {task_id} in Instance: {process_instance_id}.",
                )
    else:
        raise ApiError(
            error_code="update_task_data_error",
            message=f"Could not update task data for Instance: {process_instance_id}, and Task: {task_id}.",
        )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )


def send_bpmn_event(
    modified_process_model_identifier: str,
    process_instance_id: str,
    body: Dict,
) -> Response:
    """Send a bpmn event to a workflow."""
    process_instance = ProcessInstanceModel.query.filter(
        ProcessInstanceModel.id == int(process_instance_id)
    ).first()
    if process_instance:
        processor = ProcessInstanceProcessor(process_instance)
        processor.send_bpmn_event(body)
    else:
        raise ApiError(
            error_code="send_bpmn_event_error",
            message=f"Could not send event to Instance: {process_instance_id}",
        )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )


def mark_task_complete(
    modified_process_model_identifier: str,
    process_instance_id: str,
    task_id: str,
    body: Dict,
) -> Response:
    """Mark a task complete without executing it."""
    process_instance = ProcessInstanceModel.query.filter(
        ProcessInstanceModel.id == int(process_instance_id)
    ).first()
    if process_instance:
        processor = ProcessInstanceProcessor(process_instance)
        processor.mark_task_complete(task_id)
    else:
        raise ApiError(
            error_code="send_bpmn_event_error",
            message=f"Could not skip Task {task_id} in Instance {process_instance_id}",
        )
    return Response(
        json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
        status=200,
        mimetype="application/json",
    )


def _commit_and_push_to_git(message: str) -> None:
    """Commit_and_push_to_git."""
    if current_app.config["GIT_COMMIT_ON_SAVE"]:
        git_output = GitService.commit(message=message)
        current_app.logger.info(f"git output: {git_output}")
    else:
        current_app.logger.info("Git commit on save is disabled")


def _find_process_instance_for_me_or_raise(
    process_instance_id: int,
) -> ProcessInstanceModel:
    """_find_process_instance_for_me_or_raise."""
    process_instance: ProcessInstanceModel = (
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
                HumanTaskUserModel.id.is_not(None),
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
