import contextlib
import time
from typing import Generator
from typing import List
from typing import Optional

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_queue import (
    ProcessInstanceQueueModel,
)
from spiffworkflow_backend.services.process_instance_lock_service import (
    ProcessInstanceLockService,
)


class ProcessInstanceIsNotEnqueuedError(Exception):
    pass


class ProcessInstanceIsAlreadyLockedError(Exception):
    pass


class ProcessInstanceQueueService:
    """TODO: comment."""

    @classmethod
    def _configure_and_save_queue_entry(
        cls, process_instance: ProcessInstanceModel, queue_entry: ProcessInstanceQueueModel
    ) -> None:
        # TODO: configurable params (priority/run_at)
        queue_entry.run_at_in_seconds = round(time.time())
        queue_entry.priority = 2
        queue_entry.status = process_instance.status
        queue_entry.locked_by = None
        queue_entry.locked_at_in_seconds = None

        db.session.add(queue_entry)
        db.session.commit()

    @classmethod
    def enqueue_new_process_instance(cls, process_instance: ProcessInstanceModel) -> None:
        queue_entry = ProcessInstanceQueueModel(process_instance_id=process_instance.id)
        cls._configure_and_save_queue_entry(process_instance, queue_entry)

    @classmethod
    def _enqueue(cls, process_instance: ProcessInstanceModel) -> None:
        queue_entry = ProcessInstanceLockService.unlock(process_instance.id)
        cls._configure_and_save_queue_entry(process_instance, queue_entry)

    @classmethod
    def _dequeue(cls, process_instance: ProcessInstanceModel) -> None:
        locked_by = ProcessInstanceLockService.locked_by()

        db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.process_instance_id == process_instance.id,
            ProcessInstanceQueueModel.locked_by.is_(None),  # type: ignore
        ).update(
            {
                "locked_by": locked_by,
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

        ProcessInstanceLockService.lock(process_instance.id, queue_entry)

    @classmethod
    @contextlib.contextmanager
    def dequeued(cls, process_instance: ProcessInstanceModel) -> Generator[None, None, None]:
        reentering_lock = ProcessInstanceLockService.has_lock(process_instance.id)
        try:
            if not reentering_lock:
                cls._dequeue(process_instance)
            yield
        finally:
            if not reentering_lock:
                cls._enqueue(process_instance)

    @classmethod
    def entries_with_status(
        cls,
        status_value: str = ProcessInstanceStatus.waiting.value,
        locked_by: Optional[str] = None,
    ) -> List[ProcessInstanceQueueModel]:
        return (
            db.session.query(ProcessInstanceQueueModel)
            .filter(
                ProcessInstanceQueueModel.status == status_value,
                ProcessInstanceQueueModel.locked_by == locked_by,
            )
            .all()
        )

    @classmethod
    def peek_many(
        cls,
        status_value: str = ProcessInstanceStatus.waiting.value,
    ) -> List[int]:
        queue_entries = cls.entries_with_status(status_value, None)
        ids_with_status = [entry.process_instance_id for entry in queue_entries]
        return ids_with_status
