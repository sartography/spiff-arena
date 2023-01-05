"""APIs for dealing with process groups, process models, and process instances."""
import json
from typing import Any
from typing import Dict

import flask.wrappers
from flask import Blueprint
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask import request
from flask.wrappers import Response
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db

from spiffworkflow_backend.exceptions.process_entity_not_found_error import (
    ProcessEntityNotFoundError,
)
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance import (
    ProcessInstanceTaskDataCannotBeUpdatedError,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.models.spec_reference import SpecReferenceSchema
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService


process_api_blueprint = Blueprint("process_api", __name__)


def permissions_check(body: Dict[str, Dict[str, list[str]]]) -> flask.wrappers.Response:
    """Permissions_check."""
    if "requests_to_check" not in body:
        raise (
            ApiError(
                error_code="could_not_requests_to_check",
                message=(
                    "The key 'requests_to_check' not found at root of request body."
                ),
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


def process_list() -> Any:
    """Returns a list of all known processes.

    This includes processes that are not the
    primary process - helpful for finding possible call activities.
    """
    references = SpecReferenceCache.query.filter_by(type="process").all()
    return SpecReferenceSchema(many=True).dump(references)


def process_data_show(
    process_instance_id: int,
    process_data_identifier: str,
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    """Process_data_show."""
    process_instance = _find_process_instance_by_id_or_raise(process_instance_id)
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
                "The process instance needs to be suspended to udpate the task-data."
                f" It is currently: {process_instance.status}"
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
                    message=(
                        f"Could not find Task: {task_id} in Instance:"
                        f" {process_instance_id}."
                    ),
                )
    else:
        raise ApiError(
            error_code="update_task_data_error",
            message=(
                f"Could not update task data for Instance: {process_instance_id}, and"
                f" Task: {task_id}."
            ),
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


def manual_complete_task(
    modified_process_model_identifier: str,
    process_instance_id: str,
    task_id: str,
    body: Dict,
) -> Response:
    """Mark a task complete without executing it."""
    execute = body.get("execute", True)
    process_instance = ProcessInstanceModel.query.filter(
        ProcessInstanceModel.id == int(process_instance_id)
    ).first()
    if process_instance:
        processor = ProcessInstanceProcessor(process_instance)
        processor.manual_complete_task(task_id, execute)
    else:
        raise ApiError(
            error_code="complete_task",
            message=(
                f"Could not complete Task {task_id} in Instance {process_instance_id}"
            ),
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


def _un_modify_modified_process_model_id(modified_process_model_identifier: str) -> str:
    """Un_modify_modified_process_model_id."""
    return modified_process_model_identifier.replace(":", "/")


def _find_process_instance_by_id_or_raise(
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


# process_model_id uses forward slashes on all OSes
# this seems to return an object where process_model.id has backslashes on windows
def _get_process_model(process_model_id: str) -> ProcessModelInfo:
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


def _find_principal_or_raise() -> PrincipalModel:
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
