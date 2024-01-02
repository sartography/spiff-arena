import contextlib
import time
from collections.abc import Generator

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.process_instance_lock_service import ExpectedLockNotFoundError
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError


class ProcessInstanceIsNotEnqueuedError(Exception):
    pass


class ProcessInstanceIsAlreadyLockedError(Exception):
    pass


class ProcessInstanceQueueService:
    @classmethod
    def _configure_and_save_queue_entry(
        cls, process_instance: ProcessInstanceModel, queue_entry: ProcessInstanceQueueModel
    ) -> None:
        queue_entry.priority = 2
        queue_entry.status = process_instance.status
        queue_entry.locked_by = None
        queue_entry.locked_at_in_seconds = None

        db.session.add(queue_entry)
        db.session.commit()

    @classmethod
    def enqueue_new_process_instance(cls, process_instance: ProcessInstanceModel, run_at_in_seconds: int) -> None:
        queue_entry = ProcessInstanceQueueModel(process_instance_id=process_instance.id, run_at_in_seconds=run_at_in_seconds)
        cls._configure_and_save_queue_entry(process_instance, queue_entry)

    @classmethod
    def _enqueue(cls, process_instance: ProcessInstanceModel, additional_processing_identifier: str | None = None) -> None:
        queue_entry_id = ProcessInstanceLockService.unlock(
            process_instance.id, additional_processing_identifier=additional_processing_identifier
        )
        queue_entry = ProcessInstanceQueueModel.query.filter_by(id=queue_entry_id).first()
        if queue_entry is None:
            raise ExpectedLockNotFoundError(f"Could not find a lock for process instance: {process_instance.id}")
        current_time = round(time.time())
        if current_time > queue_entry.run_at_in_seconds:
            queue_entry.run_at_in_seconds = current_time
        cls._configure_and_save_queue_entry(process_instance, queue_entry)

    @classmethod
    def _dequeue(cls, process_instance: ProcessInstanceModel, additional_processing_identifier: str | None = None) -> None:
        locked_by = ProcessInstanceLockService.locked_by(additional_processing_identifier=additional_processing_identifier)
        current_time = round(time.time())

        db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.process_instance_id == process_instance.id,
            ProcessInstanceQueueModel.locked_by.is_(None),  # type: ignore
        ).update(
            {
                "locked_by": locked_by,
                "locked_at_in_seconds": current_time,
            }
        )

        db.session.commit()

        queue_entry = (
            db.session.query(ProcessInstanceQueueModel)
            .filter(
                ProcessInstanceQueueModel.process_instance_id == process_instance.id,
            )
            .first()
        )

        if queue_entry is None:
            raise ProcessInstanceIsNotEnqueuedError(
                f"{locked_by} cannot lock process instance {process_instance.id}. It has not been enqueued."
            )

        if queue_entry.locked_by != locked_by:
            raise ProcessInstanceIsAlreadyLockedError(
                f"{locked_by} cannot lock process instance {process_instance.id}. "
                f"It has already been locked by {queue_entry.locked_by}."
            )

        ProcessInstanceLockService.lock(
            process_instance.id, queue_entry, additional_processing_identifier=additional_processing_identifier
        )

    @classmethod
    @contextlib.contextmanager
    def dequeued(
        cls, process_instance: ProcessInstanceModel, additional_processing_identifier: str | None = None
    ) -> Generator[None, None, None]:
        reentering_lock = ProcessInstanceLockService.has_lock(
            process_instance.id, additional_processing_identifier=additional_processing_identifier
        )
        if not reentering_lock:
            # this can blow up with ProcessInstanceIsNotEnqueuedError or ProcessInstanceIsAlreadyLockedError
            # that's fine, let it bubble up. and in that case, there's no need to _enqueue / unlock
            cls._dequeue(process_instance, additional_processing_identifier=additional_processing_identifier)
        try:
            yield
        except Exception as ex:
            # these events are handled in the WorkflowExecutionService.
            # that is, we don't need to add error_detail records here, etc.
            if not isinstance(ex, WorkflowExecutionServiceError):
                ProcessInstanceTmpService.add_event_to_process_instance(
                    process_instance, ProcessInstanceEventType.process_instance_error.value, exception=ex
                )
            ErrorHandlingService.handle_error(process_instance, ex)
            raise ex
        finally:
            if not reentering_lock:
                cls._enqueue(process_instance, additional_processing_identifier=additional_processing_identifier)

    @classmethod
    def entries_with_status(
        cls,
        status_value: str,
        locked_by: str | None,
        run_at_in_seconds_threshold: int,
        min_age_in_seconds: int = 0,
    ) -> list[ProcessInstanceQueueModel]:
        return (
            db.session.query(ProcessInstanceQueueModel)
            .filter(
                ProcessInstanceQueueModel.status == status_value,
                ProcessInstanceQueueModel.updated_at_in_seconds <= round(time.time()) - min_age_in_seconds,
                # At least a minute old.
                ProcessInstanceQueueModel.locked_by == locked_by,
                ProcessInstanceQueueModel.run_at_in_seconds <= run_at_in_seconds_threshold,
            )
            .all()
        )

    @classmethod
    def peek_many(
        cls,
        status_value: str,
        run_at_in_seconds_threshold: int,
        min_age_in_seconds: int = 0,
    ) -> list[int]:
        queue_entries = cls.entries_with_status(status_value, None, run_at_in_seconds_threshold, min_age_in_seconds)
        ids_with_status = [entry.process_instance_id for entry in queue_entries]
        return ids_with_status

    @staticmethod
    def is_enqueued_to_run_in_the_future(process_instance: ProcessInstanceModel) -> bool:
        queue_entry = (
            db.session.query(ProcessInstanceQueueModel)
            .filter(ProcessInstanceQueueModel.process_instance_id == process_instance.id)
            .first()
        )

        if queue_entry is None:
            return False

        current_time = round(time.time())
        return queue_entry.run_at_in_seconds > current_time
