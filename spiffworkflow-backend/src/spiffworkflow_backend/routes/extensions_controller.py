import flask.wrappers
from flask import current_app
from SpiffWorkflow.util.deep_merge import DeepMerge # type: ignore
from spiffworkflow_backend.services.file_system_service import FileSystemService
from flask import g
from flask import jsonify
from flask import make_response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.routes.process_api_blueprint import _un_modify_modified_process_model_id
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.process_instance_processor import CustomBpmnScriptEngine
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsNotEnqueuedError
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def extension_run(
    modified_process_model_identifier: str,
    body: dict | None = None,
) -> flask.wrappers.Response:
    _raise_unless_extensions_api_enabled()

    process_model_identifier = _un_modify_modified_process_model_id(modified_process_model_identifier)

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

    if not ProcessModelService.is_allowed_to_run_as_extension(process_model):
        raise ApiError(
            error_code="invalid_process_model_extension",
            message=(
                f"Process Model '{process_model_identifier}' cannot be run as an extension. It must be in the correct"
                f" Process Group: {current_app.config['SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX']}"
            ),
            status_code=403,
        )

    process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
        process_model_identifier, g.user
    )

    processor = None
    try:
        processor = ProcessInstanceProcessor(
            process_instance, script_engine=CustomBpmnScriptEngine(use_restricted_script_engine=False)
        )
        if body and "extension_input" in body:
            processor.add_data_to_bpmn_process_instance(body['extension_input'])
        processor.do_engine_steps(save=False, execution_strategy_name="greedy")
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

    task_data = {}
    if processor is not None:
        task_data = processor.get_data()

    return make_response(jsonify(task_data), 200)


# actual frontend route
# /extensions/:anything => Extensions component
# maybe add jsonschema support when rendering the extension for primary page design
# maybe add an element for markdown as well


# backend extension ui schema for each model has something like:
# {
#     "navigation_items": [{
#         "label": "Aggregate Metadata",
#         "route": "/aggregate_metadata"
#         }
#     ],
#     "routes": {
#         "/aggregate_metadata": {
#             "header": "Aggregate Metdata",
#             "api": "aggregate_medadata"
#         }
#     }
# }
def extension_list() -> flask.wrappers.Response:
    _raise_unless_extensions_api_enabled()
    process_model_extensions = ProcessModelService.get_process_models_for_api(
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
    process_model_identifier = _un_modify_modified_process_model_id(modified_process_model_identifier)
    process_model = _get_process_model(process_model_identifier)
    files = FileSystemService.get_sorted_files(process_model)
    for f in files:
        file_contents = FileSystemService.get_data(process_model, f.name)
        f.file_contents = file_contents
    process_model.files = files
    return make_response(jsonify(process_model), 200)


def _raise_unless_extensions_api_enabled() -> None:
    if not current_app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED"]:
        raise ApiError(
            error_code="extensions_api_not_enabled",
            message="The extensions api is not enabled. Cannot run process models in this way.",
            status_code=403,
        )
