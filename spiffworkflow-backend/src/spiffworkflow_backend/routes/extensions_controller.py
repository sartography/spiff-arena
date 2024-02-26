import json
from typing import Any

import flask.wrappers
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.routes.process_api_blueprint import _un_modify_modified_process_model_id
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


def extension_run(
    modified_process_model_identifier: str,
    body: dict | None = None,
) -> flask.wrappers.Response:
    _, result = _run_extension(modified_process_model_identifier, body)
    return make_response(jsonify(result), 200)


def extension_get_data(
    query_params: str,
) -> flask.wrappers.Response:
    modified_process_model_identifier, *additional_args = query_params.split("/")
    process_model, result = _run_extension(
        modified_process_model_identifier, {"extension_input": {"additional_args": additional_args}}
    )
    response_schema = json.loads(FileSystemService.get_data(process_model, "response_schema.json"))
    headers = response_schema.get("headers", None)
    mimetype = response_schema.get("mimetype", None)
    data_extraction_path = response_schema.get("data_extraction_path", "").split(".")
    contents = _extract_data(data_extraction_path, result["task_data"])
    response = Response(
        str(contents),
        mimetype=mimetype,
        headers=headers,
        status=200,
    )
    return response


def extension_list() -> flask.wrappers.Response:
    # return an empty list if the extensions api is not enabled
    process_model_extensions = []
    if current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED"]:
        process_model_extensions = ProcessModelService.get_process_models_for_api(
            user=g.user,
            process_group_id=current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX"],
            recursive=True,
            filter_runnable_as_extension=True,
            include_files=True,
        )
    return make_response(jsonify(process_model_extensions), 200)


def extension_show(
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
    _raise_unless_extensions_api_enabled()
    process_model_identifier = _get_process_model_identifier(modified_process_model_identifier)
    process_model = _get_process_model(process_model_identifier)
    files = FileSystemService.get_sorted_files(process_model)
    for f in files:
        file_contents = FileSystemService.get_data(process_model, f.name)
        f.file_contents = file_contents
    process_model.files = files
    return make_response(jsonify(process_model), 200)


def _extract_data(keys: list[str], data: Any) -> Any:
    if len(keys) > 0 and isinstance(data, dict) and keys[0] in data:
        return _extract_data(keys[1:], data[keys[0]])
    return data


def _run_extension(
    modified_process_model_identifier: str,
    body: dict | None = None,
) -> tuple[ProcessModelInfo, dict]:
    _raise_unless_extensions_api_enabled()

    process_model_identifier = _get_process_model_identifier(modified_process_model_identifier)
    process_model = _get_process_model_or_raise(process_model_identifier)

    ui_schema_action = None
    persistence_level = "none"
    process_id_to_run = None
    if body and "ui_schema_action" in body:
        ui_schema_action = body["ui_schema_action"]
        persistence_level = ui_schema_action.get("persistence_level", "none")
        process_id_to_run = ui_schema_action.get("process_id_to_run", None)

    data_to_inject = None
    if body and "extension_input" in body:
        data_to_inject = body["extension_input"]

    processor = ProcessInstanceService.create_and_run_process_instance(
        process_model=process_model,
        persistence_level=persistence_level,
        data_to_inject=data_to_inject,
        process_id_to_run=process_id_to_run,
        user=g.user,
    )

    task_data = {}
    if processor is not None:
        task_data = processor.get_data()
    result: dict[str, Any] = {"task_data": task_data}

    if ui_schema_action:
        if "results_markdown_filename" in ui_schema_action:
            file_contents = SpecFileService.get_data(process_model, ui_schema_action["results_markdown_filename"]).decode("utf-8")
            form_contents = JinjaService.render_jinja_template(file_contents, task_data=task_data)
            result["rendered_results_markdown"] = form_contents

    return (process_model, result)


def _raise_unless_extensions_api_enabled() -> None:
    if not current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED"]:
        raise ApiError(
            error_code="extensions_api_not_enabled",
            message="The extensions api is not enabled. Cannot run process models in this way.",
            status_code=403,
        )


def _get_process_model_identifier(modified_process_model_identifier: str) -> str:
    process_model_identifier = _un_modify_modified_process_model_id(modified_process_model_identifier)
    return _add_extension_group_identifier_it_not_present(process_model_identifier)


def _add_extension_group_identifier_it_not_present(process_model_identifier: str) -> str:
    """Adds the extension prefix if it does not already exist on the process model identifier.

    This allows for the frontend to use just process model identifier without having to know the extension group
    or having to add it to the uischema json which would have numerous other issues. Instead let backend take care of that.
    """
    extension_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX"]
    if process_model_identifier.startswith(f"{extension_prefix}/"):
        return process_model_identifier
    return f"{extension_prefix}/{process_model_identifier}"


def _get_process_model_or_raise(process_model_identifier: str) -> ProcessModelInfo:
    try:
        process_model = _get_process_model(process_model_identifier)
    except ApiError as ex:
        if ex.error_code == "process_model_cannot_be_found":
            # if process_model_identifier.startswith(current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX"])
            raise ApiError(
                error_code="invalid_process_model_extension",
                message=(
                    f"Process Model '{process_model_identifier}' could not be found as an extension. It must be in the"
                    " correct Process Group:"
                    f" {current_app.config['SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX']}"
                ),
                status_code=403,
            ) from ex
        raise ex

    if process_model.primary_file_name is None:
        raise ApiError(
            error_code="process_model_missing_primary_bpmn_file",
            message=(
                f"Process Model '{process_model_identifier}' does not have a primary"
                " bpmn file. One must be set in order to instantiate this model."
            ),
            status_code=400,
        )
    return process_model
