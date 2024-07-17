import contextlib
import time
from collections.abc import Generator

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceCannotBeRunError
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
    def _enqueue(cls, process_instance: ProcessInstanceModel) -> None:
        queue_entry_id = ProcessInstanceLockService.unlock(process_instance.id)
        queue_entry = ProcessInstanceQueueModel.query.filter_by(id=queue_entry_id).first()
        if queue_entry is None:
            raise ExpectedLockNotFoundError(f"Could not find a lock for process instance: {process_instance.id}")
        current_time = round(time.time())
        if current_time > queue_entry.run_at_in_seconds:
            queue_entry.run_at_in_seconds = current_time
        cls._configure_and_save_queue_entry(process_instance, queue_entry)

    @classmethod
    def _dequeue(cls, process_instance: ProcessInstanceModel) -> None:
        locked_by = ProcessInstanceLockService.locked_by()
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
            message = f"It has already been locked by {queue_entry.locked_by}."
            if queue_entry.locked_by is None:
                message = "It was locked by something else when we tried to lock it in the db, but it has since been unlocked."
            raise ProcessInstanceIsAlreadyLockedError(
                f"{locked_by} cannot lock process instance {process_instance.id}. {message}"
            )

        ProcessInstanceLockService.lock(process_instance.id, queue_entry)

    @classmethod
    def _dequeue_with_retries(
        cls,
        process_instance: ProcessInstanceModel,
        max_attempts: int = 1,
    ) -> None:
        attempt = 1
        backoff_factor = 2
        while True:
            try:
                return cls._dequeue(process_instance)
            except ProcessInstanceIsAlreadyLockedError as exception:
                if attempt >= max_attempts:
                    raise exception
                time.sleep(backoff_factor**attempt)
                attempt += 1

    @classmethod
    @contextlib.contextmanager
    def dequeued(
        cls,
        process_instance: ProcessInstanceModel,
        max_attempts: int = 1,
        ignore_cannot_be_run_error: bool = False,
    ) -> Generator[None, None, None]:
        reentering_lock = ProcessInstanceLockService.has_lock(process_instance.id)

        if not reentering_lock:
            # this can blow up with ProcessInstanceIsNotEnqueuedError or ProcessInstanceIsAlreadyLockedError
            # that's fine, let it bubble up. and in that case, there's no need to _enqueue / unlock
            cls._dequeue_with_retries(process_instance, max_attempts=max_attempts)
        try:
            yield
        except ProcessInstanceCannotBeRunError as ex:
            if not ignore_cannot_be_run_error:
                raise ex
        except Exception as ex:
            # these events are handled in the WorkflowExecutionService.
            # that is, we don't need to add error_detail records here, etc.
            if not isinstance(ex, WorkflowExecutionServiceError):
                ProcessInstanceTmpService.add_event_to_process_instance(
                    process_instance, ProcessInstanceEventType.process_instance_error.value, exception=ex
                )

            # we call dequeued multiple times but we want this code to only happen once.
            # assume that if we are not reentering_lock then this is the top level call and should be the one to handle the error.
            if not reentering_lock:
                ErrorHandlingService.handle_error(process_instance, ex)
            raise ex
        finally:
            if not reentering_lock:
                cls._enqueue(process_instance)

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
