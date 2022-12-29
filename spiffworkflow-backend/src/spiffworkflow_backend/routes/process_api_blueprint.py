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
from spiffworkflow_backend.services.git_service import GitCommandError
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


def user_group_list_for_current_user() -> flask.wrappers.Response:
    """User_group_list_for_current_user."""
    groups = g.user.groups
    # TODO: filter out the default group and have a way to know what is the default group
    group_identifiers = [i.identifier for i in groups if i.identifier != "everybody"]
    return make_response(jsonify(sorted(group_identifiers)), 200)


def process_list() -> Any:
    """Returns a list of all known processes.

    This includes processes that are not the
    primary process - helpful for finding possible call activities.
    """
    references = SpecReferenceCache.query.filter_by(type="process").all()
    return SpecReferenceSchema(many=True).dump(references)


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
    process_model = _get_process_model(process_model_identifier)
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


def _get_process_instance(
    modified_process_model_identifier: str,
    process_instance: ProcessInstanceModel,
    process_identifier: Optional[str] = None,
) -> flask.wrappers.Response:
    """_get_process_instance."""
    process_model_identifier = modified_process_model_identifier.replace(":", "/")
    try:
        current_version_control_revision = GitService.get_current_revision()
    except GitCommandError:
        current_version_control_revision = ""

    process_model_with_diagram = None
    name_of_file_with_diagram = None
    if process_identifier:
        spec_reference = SpecReferenceCache.query.filter_by(
            identifier=process_identifier, type="process"
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
        process_model_with_diagram = _get_process_model(process_model_identifier)
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


def _get_file_from_request() -> Any:
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


def _get_spiff_task_from_process_instance(
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
