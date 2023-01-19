"""APIs for dealing with process groups, process models, and process instances."""
import json
import os
import re
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import connexion  # type: ignore
import flask.wrappers
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response
from werkzeug.datastructures import FileStorage

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.interfaces import IdToProcessGroupMapping
from spiffworkflow_backend.models.file import FileSchema
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.routes.process_api_blueprint import _commit_and_push_to_git
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.routes.process_api_blueprint import (
    _un_modify_modified_process_model_id,
)
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.git_service import MissingGitConfigsError
from spiffworkflow_backend.services.process_instance_report_service import (
    ProcessInstanceReportNotFoundError,
)
from spiffworkflow_backend.services.process_instance_report_service import (
    ProcessInstanceReportService,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.process_model_service import (
    ProcessModelWithInstancesNotDeletableError,
)
from spiffworkflow_backend.services.spec_file_service import (
    ProcessModelFileInvalidError,
)
from spiffworkflow_backend.services.spec_file_service import SpecFileService


def process_model_create(
    modified_process_group_id: str, body: Dict[str, Union[str, bool, int, None, list]]
) -> flask.wrappers.Response:
    """Process_model_create."""
    body_include_list = [
        "id",
        "display_name",
        "primary_file_name",
        "primary_process_id",
        "description",
        "metadata_extraction_paths",
        "fault_or_suspend_on_exception",
        "exception_notification_addresses",
    ]
    body_filtered = {
        include_item: body[include_item]
        for include_item in body_include_list
        if include_item in body
    }

    _get_process_group_from_modified_identifier(modified_process_group_id)

    process_model_info = ProcessModelInfo(**body_filtered)  # type: ignore
    if process_model_info is None:
        raise ApiError(
            error_code="process_model_could_not_be_created",
            message=f"Process Model could not be created from given body: {body}",
            status_code=400,
        )

    if ProcessModelService.is_process_model_identifier(process_model_info.id):
        raise ApiError(
            error_code="process_model_with_id_already_exists",
            message=(
                f"Process Model with given id already exists: {process_model_info.id}"
            ),
            status_code=400,
        )

    if ProcessModelService.is_process_group_identifier(process_model_info.id):
        raise ApiError(
            error_code="process_group_with_id_already_exists",
            message=(
                f"Process Group with given id already exists: {process_model_info.id}"
            ),
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
    try:
        ProcessModelService().process_model_delete(process_model_identifier)
    except ProcessModelWithInstancesNotDeletableError as exception:
        raise ApiError(
            error_code="existing_instances",
            message=str(exception),
            status_code=400,
        ) from exception

    _commit_and_push_to_git(
        f"User: {g.user.username} deleted process model {process_model_identifier}"
    )
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_model_update(
    modified_process_model_identifier: str,
    body: Dict[str, Union[str, bool, int, None, list]],
) -> Any:
    """Process_model_update."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    body_include_list = [
        "display_name",
        "primary_file_name",
        "primary_process_id",
        "description",
        "metadata_extraction_paths",
        "fault_or_suspend_on_exception",
        "exception_notification_addresses",
    ]
    body_filtered = {
        include_item: body[include_item]
        for include_item in body_include_list
        if include_item in body
    }

    process_model = _get_process_model(process_model_identifier)
    ProcessModelService.update_process_model(process_model, body_filtered)
    _commit_and_push_to_git(
        f"User: {g.user.username} updated process model {process_model_identifier}"
    )
    return ProcessModelInfoSchema().dump(process_model)


def process_model_show(
    modified_process_model_identifier: str, include_file_references: bool = False
) -> Any:
    """Process_model_show."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = _get_process_model(process_model_identifier)
    files = sorted(
        SpecFileService.get_files(process_model),
        key=lambda f: "" if f.name == process_model.primary_file_name else f.sort_index,
    )
    process_model.files = files

    if include_file_references:
        for file in process_model.files:
            file.references = SpecFileService.get_references_for_file(
                file, process_model
            )

    process_model.parent_groups = ProcessModelService.get_parent_group_array(
        process_model.id
    )
    return make_response(jsonify(process_model), 200)


def process_model_move(
    modified_process_model_identifier: str, new_location: str
) -> flask.wrappers.Response:
    """Process_model_move."""
    original_process_model_id = _un_modify_modified_process_model_id(
        modified_process_model_identifier
    )
    new_process_model = ProcessModelService().process_model_move(
        original_process_model_id, new_location
    )
    _commit_and_push_to_git(
        f"User: {g.user.username} moved process model {original_process_model_id} to"
        f" {new_process_model.id}"
    )
    return make_response(jsonify(new_process_model), 200)


def process_model_publish(
    modified_process_model_identifier: str, branch_to_update: Optional[str] = None
) -> flask.wrappers.Response:
    """Process_model_publish."""
    if branch_to_update is None:
        branch_to_update = current_app.config["GIT_BRANCH_TO_PUBLISH_TO"]
    if branch_to_update is None:
        raise MissingGitConfigsError(
            "Missing config for GIT_BRANCH_TO_PUBLISH_TO. "
            "This is required for publishing process models"
        )
    process_model_identifier = _un_modify_modified_process_model_id(
        modified_process_model_identifier
    )
    pr_url = GitService().publish(process_model_identifier, branch_to_update)
    data = {"ok": True, "pr_url": pr_url}
    return Response(json.dumps(data), status=200, mimetype="application/json")


def process_model_list(
    process_group_identifier: Optional[str] = None,
    recursive: Optional[bool] = False,
    filter_runnable_by_user: Optional[bool] = False,
    include_parent_groups: Optional[bool] = False,
    page: int = 1,
    per_page: int = 100,
) -> flask.wrappers.Response:
    """Process model list!"""
    process_models = ProcessModelService.get_process_models(
        process_group_id=process_group_identifier,
        recursive=recursive,
        filter_runnable_by_user=filter_runnable_by_user,
    )
    process_models_to_return = ProcessModelService().get_batch(
        process_models, page=page, per_page=per_page
    )

    if include_parent_groups:
        process_group_cache = IdToProcessGroupMapping({})
        for process_model in process_models_to_return:
            parent_group_lites_with_cache = (
                ProcessModelService.get_parent_group_array_and_cache_it(
                    process_model.id, process_group_cache
                )
            )
            process_model.parent_groups = parent_group_lites_with_cache[
                "process_groups"
            ]

    pages = len(process_models) // per_page
    remainder = len(process_models) % per_page
    if remainder > 0:
        pages += 1
    response_json = {
        "results": process_models_to_return,
        "pagination": {
            "count": len(process_models_to_return),
            "total": len(process_models),
            "pages": pages,
        },
    }
    return make_response(jsonify(response_json), 200)


def process_model_file_update(
    modified_process_model_identifier: str, file_name: str
) -> flask.wrappers.Response:
    """Process_model_file_update."""
    message = f"User: {g.user.username} clicked save for"
    return _create_or_update_process_model_file(
        modified_process_model_identifier, message, 200
    )


def process_model_file_delete(
    modified_process_model_identifier: str, file_name: str
) -> flask.wrappers.Response:
    """Process_model_file_delete."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = _get_process_model(process_model_identifier)
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
        f"User: {g.user.username} deleted process model file"
        f" {process_model_identifier}/{file_name}"
    )
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def process_model_file_create(
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_model_file_create."""
    message = f"User: {g.user.username} added process model file"
    return _create_or_update_process_model_file(
        modified_process_model_identifier, message, 201
    )


def process_model_file_show(
    modified_process_model_identifier: str, file_name: str
) -> Any:
    """Process_model_file_show."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = _get_process_model(process_model_identifier)
    files = SpecFileService.get_files(process_model, file_name)
    if len(files) == 0:
        raise ApiError(
            error_code="unknown file",
            message=(
                f"No information exists for file {file_name}"
                f" it does not exist in workflow {process_model_identifier}."
            ),
            status_code=404,
        )

    file = files[0]
    file_contents = SpecFileService.get_data(process_model, file.name)
    file.file_contents = file_contents
    file.process_model_id = process_model.id
    return FileSchema().dump(file)


#   {
#       "natural_language_text": "Create a bug tracker process model \
#           with a bug-details form that collects summary, description, and priority"
#   }
def process_model_create_with_natural_language(
    modified_process_group_id: str, body: Dict[str, str]
) -> flask.wrappers.Response:
    """Process_model_create_with_natural_language."""
    pattern = re.compile(
        r"Create a (?P<pm_name>.*?) process model with a (?P<form_name>.*?) form that"
        r" collects (?P<columns>.*)"
    )
    match = pattern.match(body["natural_language_text"])
    if match is None:
        raise ApiError(
            error_code="natural_language_text_not_yet_supported",
            message=(
                "Natural language text is not yet supported. Please use the form:"
                f" {pattern.pattern}"
            ),
            status_code=400,
        )
    process_model_display_name = match.group("pm_name")
    process_model_identifier = re.sub(r"[ _]", "-", process_model_display_name)
    process_model_identifier = re.sub(r"-{2,}", "-", process_model_identifier).lower()

    form_name = match.group("form_name")
    form_identifier = re.sub(r"[ _]", "-", form_name)
    form_identifier = re.sub(r"-{2,}", "-", form_identifier).lower()

    column_names = match.group("columns")
    columns = re.sub(r"(, (and )?)", ",", column_names).split(",")

    process_group = _get_process_group_from_modified_identifier(
        modified_process_group_id
    )
    qualified_process_model_identifier = (
        f"{process_group.id}/{process_model_identifier}"
    )

    metadata_extraction_paths = []
    for column in columns:
        metadata_extraction_paths.append({"key": column, "path": column})

    process_model_attributes = {
        "id": qualified_process_model_identifier,
        "display_name": process_model_display_name,
        "description": None,
        "metadata_extraction_paths": metadata_extraction_paths,
    }

    process_model_info = ProcessModelInfo(**process_model_attributes)  # type: ignore
    if process_model_info is None:
        raise ApiError(
            error_code="process_model_could_not_be_created",
            message=f"Process Model could not be created from given body: {body}",
            status_code=400,
        )

    bpmn_template_file = os.path.join(
        current_app.root_path, "templates", "basic_with_user_task_template.bpmn"
    )
    if not os.path.exists(bpmn_template_file):
        raise ApiError(
            error_code="bpmn_template_file_does_not_exist",
            message="Could not find the bpmn template file to create process model.",
            status_code=500,
        )

    ProcessModelService.add_process_model(process_model_info)
    bpmn_process_identifier = f"{process_model_identifier}_process"
    bpmn_template_contents = ""
    with open(bpmn_template_file, encoding="utf-8") as f:
        bpmn_template_contents = f.read()

    bpmn_template_contents = bpmn_template_contents.replace(
        "natural_language_process_id_template", bpmn_process_identifier
    )
    bpmn_template_contents = bpmn_template_contents.replace(
        "form-identifier-id-template", form_identifier
    )

    form_uischema_json: dict = {"ui:order": columns}

    form_properties: dict = {}
    for column in columns:
        form_properties[column] = {
            "type": "string",
            "title": column,
        }
    form_schema_json = {
        "title": form_identifier,
        "description": "",
        "properties": form_properties,
        "required": [],
    }

    SpecFileService.add_file(
        process_model_info,
        f"{process_model_identifier}.bpmn",
        str.encode(bpmn_template_contents),
    )
    SpecFileService.add_file(
        process_model_info,
        f"{form_identifier}-schema.json",
        str.encode(json.dumps(form_schema_json)),
    )
    SpecFileService.add_file(
        process_model_info,
        f"{form_identifier}-uischema.json",
        str.encode(json.dumps(form_uischema_json)),
    )

    _commit_and_push_to_git(
        f"User: {g.user.username} created process model via natural language:"
        f" {process_model_info.id}"
    )

    default_report_metadata = ProcessInstanceReportService.system_metadata_map(
        "default"
    )
    if default_report_metadata is None:
        raise ProcessInstanceReportNotFoundError(
            "Could not find a report with identifier 'default'"
        )
    for column in columns:
        default_report_metadata["columns"].append(
            {"Header": column, "accessor": column, "filterable": True}
        )
    ProcessInstanceReportModel.create_report(
        identifier=process_model_identifier,
        user=g.user,
        report_metadata=default_report_metadata,
    )

    return Response(
        json.dumps(ProcessModelInfoSchema().dump(process_model_info)),
        status=201,
        mimetype="application/json",
    )


def _get_file_from_request() -> FileStorage:
    """Get_file_from_request."""
    request_file: FileStorage = connexion.request.files.get("file")
    if not request_file:
        raise ApiError(
            error_code="no_file_given",
            message="Given request does not contain a file",
            status_code=400,
        )
    return request_file


def _get_process_group_from_modified_identifier(
    modified_process_group_id: str,
) -> ProcessGroup:
    """_get_process_group_from_modified_identifier."""
    if modified_process_group_id is None:
        raise ApiError(
            error_code="process_group_id_not_specified",
            message=(
                "Process Model could not be created when process_group_id path param is"
                " unspecified"
            ),
            status_code=400,
        )

    unmodified_process_group_id = _un_modify_modified_process_model_id(
        modified_process_group_id
    )
    process_group = ProcessModelService.get_process_group(unmodified_process_group_id)
    if process_group is None:
        raise ApiError(
            error_code="process_model_could_not_be_created",
            message=(
                "Process Model could not be created from given body because Process"
                f" Group could not be found: {unmodified_process_group_id}"
            ),
            status_code=400,
        )
    return process_group


def _create_or_update_process_model_file(
    modified_process_model_identifier: str,
    message_for_git_commit: str,
    http_status_to_return: int,
) -> flask.wrappers.Response:
    """_create_or_update_process_model_file."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    process_model = _get_process_model(process_model_identifier)
    request_file = _get_file_from_request()

    # for mypy
    request_file_contents = request_file.stream.read()
    if not request_file_contents:
        raise ApiError(
            error_code="file_contents_empty",
            message="Given request file does not have any content",
            status_code=400,
        )
    if not request_file.filename:
        raise ApiError(
            error_code="could_not_get_filename",
            message="Could not get filename from request",
            status_code=400,
        )

    file = None
    try:
        file = SpecFileService.update_file(
            process_model, request_file.filename, request_file_contents
        )
    except ProcessModelFileInvalidError as exception:
        raise (
            ApiError(
                error_code="process_model_file_invalid",
                message=(
                    f"Invalid Process model file: {request_file.filename}."
                    f" Received error: {str(exception)}"
                ),
                status_code=400,
            )
        ) from exception
    file_contents = SpecFileService.get_data(process_model, file.name)
    file.file_contents = file_contents
    file.process_model_id = process_model.id
    _commit_and_push_to_git(
        f"{message_for_git_commit} {process_model_identifier}/{file.name}"
    )

    return Response(
        json.dumps(FileSchema().dump(file)),
        status=http_status_to_return,
        mimetype="application/json",
    )
