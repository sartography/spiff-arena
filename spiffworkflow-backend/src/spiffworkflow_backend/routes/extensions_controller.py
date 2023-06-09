from flask import make_response
from flask import jsonify
from flask import g
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsNotEnqueuedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model
from spiffworkflow_backend.routes.process_api_blueprint import _un_modify_modified_process_model_id
import flask.wrappers
from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.workflow_execution_service import execution_strategy_named


def extension_run(
    modified_process_model_identifier: str,
) -> flask.wrappers.Response:
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

    process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
        process_model_identifier, g.user
    )

    processor = None
    try:
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=False, execution_strategy_name='greedy')
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
