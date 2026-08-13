from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_triggerable_process_model import MessageTriggerableProcessModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceCannotBeRunError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.operation_instrumentation_service import OperationInstrumentation
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability


class BackgroundOperationOutcome(str, Enum):
    success = "success"
    skipped = "skipped"
    locked = "locked"


class ProcessInstanceOperationError(Exception):
    pass


@dataclass(frozen=True)
class RunQueuedProcessInstanceResult:
    outcome: BackgroundOperationOutcome
    process_instance_id: int
    task_guid: str | None
    message: str | None = None
    exception: str | None = None
    should_requeue: bool = False
    requeue_task_guid: str | None = None

    def celery_result(self) -> dict[str, object]:
        result: dict[str, object] = {
            "ok": self.outcome != BackgroundOperationOutcome.locked,
            "process_instance_id": self.process_instance_id,
            "task_guid": self.task_guid,
        }
        if self.message is not None:
            result["message"] = self.message
        if self.exception is not None:
            result["exception"] = self.exception
        return result


@dataclass(frozen=True)
class StartReservedProcessFromMessageResult:
    outcome: BackgroundOperationOutcome
    process_instance_id: int
    message_instance_id: int
    receiver_message_instance_id: int

    def celery_result(self) -> dict[str, object]:
        return {
            "ok": True,
            "process_instance_id": self.process_instance_id,
            "message_instance_id": self.message_instance_id,
            "receiver_message_instance_id": self.receiver_message_instance_id,
        }


def run_queued_process_instance(
    process_instance_id: int,
    task_guid: str | None = None,
    *,
    instrumentation: OperationInstrumentation | None = None,
) -> RunQueuedProcessInstanceResult:
    instrumentation = instrumentation or OperationInstrumentation()
    ProcessInstanceLockService.set_thread_local_locking_context("bg:process-run")
    with instrumentation.phase("load"):
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()

    if process_instance is None:
        return RunQueuedProcessInstanceResult(
            BackgroundOperationOutcome.skipped,
            process_instance_id,
            task_guid,
            message="Skipped because the process instance no longer exists in the database. It could have been deleted.",
        )
    if task_guid is None and ProcessInstanceQueueService.is_enqueued_to_run_in_the_future(process_instance):
        return RunQueuedProcessInstanceResult(
            BackgroundOperationOutcome.skipped,
            process_instance_id,
            task_guid,
            message="Skipped because the process instance is set to run in the future.",
        )

    try:
        task_guid_for_requeueing = task_guid
        future_task_was_rescheduled = False
        with instrumentation.phase("lock"), ProcessInstanceQueueService.dequeued(process_instance):
            with instrumentation.phase("engine_run"):
                ProcessInstanceService.run_process_instance_with_runtime(
                    process_instance,
                    execution_strategy_name="run_current_ready_tasks",
                    should_schedule_waiting_timer_events=False,
                )
                _runtime, task_runnability = ProcessInstanceService.run_process_instance_with_runtime(
                    process_instance,
                    execution_strategy_name="queue_instructions_for_end_user",
                )
            if task_guid is not None:
                completed_task_model = (
                    TaskModel.query.filter_by(guid=task_guid)
                    .filter(TaskModel.state.in_(["COMPLETED", "ERROR", "CANCELLED"]))  # type: ignore
                    .first()
                )
                future_task = FutureTaskModel.query.filter_by(completed=False, guid=task_guid).first()
                if completed_task_model is not None and future_task is not None:
                    with instrumentation.phase("persistence"):
                        future_task.completed = True
                        db.session.add(future_task)
                        db.session.commit()
                    task_guid_for_requeueing = None
                elif future_task is not None and future_task.run_at_in_seconds > round(time.time()):
                    future_task_was_rescheduled = True
                    task_guid_for_requeueing = None
        should_requeue = task_runnability == TaskRunnability.has_ready_tasks and not future_task_was_rescheduled
        return RunQueuedProcessInstanceResult(
            BackgroundOperationOutcome.success,
            process_instance_id,
            task_guid,
            should_requeue=should_requeue,
            requeue_task_guid=task_guid_for_requeueing if should_requeue else None,
        )
    except (ProcessInstanceIsAlreadyLockedError, ProcessInstanceCannotBeRunError) as exception:
        return RunQueuedProcessInstanceResult(
            BackgroundOperationOutcome.locked,
            process_instance_id,
            task_guid,
            exception=str(exception),
        )
    except Exception as exception:
        with instrumentation.phase("persistence"):
            db.session.rollback()
            db.session.add(process_instance)
            db.session.commit()
        raise ProcessInstanceOperationError(
            f"Error running process_instance {process_instance_id} task_guid {task_guid}. {str(exception)}"
        ) from exception


def start_reserved_process_from_message(
    process_instance_id: int,
    message_instance_id: int,
    message_triggerable_process_model_id: int,
    *,
    instrumentation: OperationInstrumentation | None = None,
) -> StartReservedProcessFromMessageResult:
    instrumentation = instrumentation or OperationInstrumentation()
    ProcessInstanceLockService.set_thread_local_locking_context("bg:message-start")
    with instrumentation.phase("load"):
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        message_instance = MessageInstanceModel.query.filter_by(id=message_instance_id).first()
        message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(
            id=message_triggerable_process_model_id
        ).first()
    if process_instance is None:
        raise ProcessInstanceOperationError(f"Could not find reserved process instance with id {process_instance_id}")
    if message_instance is None:
        raise ProcessInstanceOperationError(f"Could not find message instance with id {message_instance_id}")
    if message_triggerable_process_model is None:
        raise ProcessInstanceOperationError(
            f"Could not find message-triggerable process model with id {message_triggerable_process_model_id}"
        )

    try:
        with instrumentation.phase("engine_run"):
            receiver_message = MessageService.start_reserved_process_from_message(
                process_instance,
                message_instance,
                message_triggerable_process_model,
            )
        return StartReservedProcessFromMessageResult(
            BackgroundOperationOutcome.success,
            process_instance_id,
            message_instance_id,
            receiver_message.id,
        )
    except Exception as exception:
        with instrumentation.phase("persistence"):
            db.session.rollback()
        raise ProcessInstanceOperationError(
            f"Error starting reserved process instance {process_instance_id} from message instance {message_instance_id}. "
            f"{str(exception)}"
        ) from exception
