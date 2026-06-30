import json
import uuid
from dataclasses import dataclass
from typing import Any

import sentry_sdk
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.spiff.specs.defaults import ServiceTask  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import should_queue_process_instance
from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.helpers.spiff_enum import ProcessInstanceExecutionMode
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.custom_service_task import CustomServiceTask
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.service_task_delegate import ServiceTaskDelegate
from spiffworkflow_backend.services.service_task_delegate import ServiceTaskDelegateService


@dataclass
class ServiceTaskCallbackResult:
    process_instance: Any
    processor: Any
    next_task: SpiffTask | None
    callback_outcome: dict[str, Any] | None = None


class ServiceTaskService:
    @classmethod
    def complete_waiting_callback(
        cls,
        process_instance_id: int,
        task_guid: str,
        content: dict[str, Any] | None,
        user: Any,
        execution_mode: str | None = None,
    ) -> ServiceTaskCallbackResult:
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        if process_instance is None:
            raise ApiError(
                error_code="process_instance_cannot_be_found",
                message=f"Process instance cannot be found: {process_instance_id}",
                status_code=400,
            )

        error = None
        should_queue_for_celery = should_queue_process_instance(execution_mode)
        with sentry_sdk.start_span(op="task", name="complete_service_task_callback"):
            with ProcessInstanceQueueService.dequeued(process_instance, max_attempts=3):
                if ProcessInstanceMigrator.run(process_instance):
                    db.session.refresh(process_instance)

                processor = ProcessInstanceProcessor(
                    process_instance, workflow_completed_handler=ProcessInstanceService.schedule_next_process_model_cycle
                )
                spiff_task = cls._get_spiff_task_from_processor(task_guid, processor)

                if spiff_task.state == TaskState.STARTED and isinstance(spiff_task.task_spec, ServiceTask):
                    callback_content = content or {}
                    try:
                        cls._check_for_callback_errors(spiff_task, callback_content)
                    except WorkflowTaskException as exception:
                        callback_outcome = cls._schedule_retry_for_callback_error(processor, spiff_task, exception)
                        if callback_outcome is not None:
                            return ServiceTaskCallbackResult(
                                process_instance=process_instance,
                                processor=processor,
                                next_task=None,
                                callback_outcome=callback_outcome,
                            )
                        raise

                    result_variable = spiff_task.task_spec.result_variable
                    callback_result = cls._get_callback_body(callback_content)
                    if result_variable:
                        spiff_task.data[result_variable] = callback_result

                    processor.complete_task(spiff_task, user)

                    if should_queue_for_celery:
                        processor.save()
                    else:
                        execution_strategy_name = None
                        if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
                            execution_strategy_name = "greedy"
                        processor.do_engine_steps(save=True, execution_strategy_name=execution_strategy_name)
                else:
                    error = ApiError(
                        error_code="not_waiting_for_callback",
                        message="This process instance is not waiting for a callback.",
                        status_code=400,
                    )
            if error:
                raise error
            if should_queue_for_celery:
                queue_process_instance_if_appropriate(process_instance, execution_mode)
            return ServiceTaskCallbackResult(
                process_instance=process_instance,
                processor=processor,
                next_task=processor.next_task(),
            )

    @classmethod
    def _schedule_retry_for_callback_error(
        cls,
        processor: ProcessInstanceProcessor,
        spiff_task: SpiffTask,
        exception: WorkflowTaskException,
    ) -> dict[str, Any] | None:
        if not isinstance(spiff_task.task_spec, CustomServiceTask):
            return None
        if not spiff_task.task_spec.should_retry(spiff_task, exception):
            if spiff_task.task_spec.retries is not None:
                spiff_task.task_spec.log_terminal_failure(spiff_task, exception)
                spiff_task._set_state(TaskState.ERROR)
                processor.do_engine_steps(save=True, needs_dequeue=False)
            return None

        spiff_task.task_spec.schedule_retry(spiff_task)
        callback_outcome = cls._retry_scheduled_callback_outcome(spiff_task)
        processor.do_engine_steps(save=True, needs_dequeue=False)
        return callback_outcome

    @staticmethod
    def _retry_scheduled_callback_outcome(spiff_task: SpiffTask) -> dict[str, Any]:
        task_spec = spiff_task.task_spec
        if not isinstance(task_spec, CustomServiceTask):
            raise ValueError("Retry callback outcomes require a CustomServiceTask.")

        retries_attempted = task_spec.get_retries_attempted(spiff_task)
        max_retries = int(task_spec.retries or 0)
        return {
            "status": "retry_scheduled",
            "task_guid": str(spiff_task.id),
            "retry_at": spiff_task.internal_data.get(CustomServiceTask.RETRY_AT_KEY),
            "retries_attempted": retries_attempted,
            "retries_remaining": max(max_retries - retries_attempted, 0),
            "max_retries": max_retries,
        }

    @staticmethod
    def _check_for_callback_errors(spiff_task: SpiffTask, content: dict[str, Any]) -> None:
        try:
            ServiceTaskDelegate.check_for_errors(
                spiff_task=spiff_task,
                parsed_response=content,
                status_code=200,
                response_text=json.dumps(content),
                operator_identifier=spiff_task.task_spec.operation_name,
            )
        except Exception as e:
            wte = WorkflowTaskException("Error executing Service Task", task=spiff_task, exception=e)
            wte.add_note(str(e))
            raise wte from e

    @staticmethod
    def _get_callback_body(content: dict[str, Any]) -> Any:
        command_response = content.get("command_response")
        if not isinstance(command_response, dict) or "body" not in command_response:
            raise ApiError(
                error_code="invalid_callback_body",
                message="Service task callbacks must provide a command_response.body value.",
                status_code=400,
            )

        body = command_response["body"]
        mimetype = command_response.get("mimetype")
        if isinstance(body, str) and mimetype == "application/json":
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return body
        return body

    @staticmethod
    def _get_spiff_task_from_processor(task_guid: str, processor: Any) -> SpiffTask:
        task_uuid = uuid.UUID(task_guid)
        spiff_task = processor.bpmn_process_instance.get_task_from_id(task_uuid)

        if spiff_task is None:
            raise ApiError(
                error_code="callback_not_found",
                message=f"No task found with guid '{task_guid}'. The task may have already completed or the guid is invalid.",
                status_code=400,
            )
        return spiff_task

    @staticmethod
    def available_connectors() -> Any:
        return ServiceTaskDelegateService.available_connectors()

    @staticmethod
    def authentication_list() -> Any:
        return ServiceTaskDelegateService.authentication_list()
